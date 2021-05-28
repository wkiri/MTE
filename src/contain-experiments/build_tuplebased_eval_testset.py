# This code produces a tuple-based evaluation set that is shared for different relation extraction model. This is to make sure that a consistent evaluation set is used. 
# This code requires python2 and being run on MILA
# Before running this code, go to MILA and activate the virtualenv at /home/yzhuang/env. Run a StanfordCoreNLP server. Also need to modify config.py to constraint the relation and types of ners 

import sys, os, io, json, argparse, glob, re
assert sys.version[0] == "2"
# The following two lines make CoreNLP happy
reload(sys)
sys.setdefaultencoding('UTF8')
from pycorenlp import StanfordCoreNLP
from os.path import abspath, dirname, join, exists
from my_name_utils import canonical_target_name, canonical_elemin_name

def parse(txt_file, ann_file, accept_entities):
    with open(txt_file) as text_file, open(ann_file) as ann_file:
        texts = text_file.read().decode('utf8')
        text_file.close()
        anns = map(lambda x: x.strip().split('\t'), ann_file)
        anns = filter(lambda x: len(x) > 2, anns)
        # FIXME: ignoring the annotations which are complex

        anns = filter(lambda x: ';' not in x[1], anns)

        # FIXME: some annotations' spread have been split into many, separated by ; ignoring them

        def __parse_ann(ann):
            spec = ann[1].split()
            entity_type = spec[0]
            ann_id = ann[0]
            markers = list(map(lambda x: int(x), spec[1:]))
            # t = ' '.join([texts[begin:end] for begin,end in zip(markers[::2], markers[1::2])])
            t = texts[markers[0]:markers[1]]
            if not t == ann[2]:
                print("Error: Annotation mis-match, file=%s, ann=%s, text=%s" % (txt_file, str(ann), t))
                return None
            return (entity_type, markers, t, ann_id)

        anns = map(__parse_ann, anns)  # format
        anns = filter(lambda x: x, anns)  # skip None

        # building a tree index for easy accessing
        tree = {}
        for entity_type, pos, name, ann_id in anns:
            if entity_type in accept_entities:
                begin, end = pos[0], pos[1]
                if begin not in tree:
                    tree[begin] = {}
                node = tree[begin]
                if end not in node:
                    node[end] = []
                node[end].append(ann_id)

        # Re-read file in without decoding it
        text_file = open(txt_file)
        texts = text_file.read()
        text_file.close()
        return texts, tree


def include_brat_ann(entities, brat_tree):
    continue_ann, continue_ann_end, continue_ann_begin = None, None, None
    for e in entities:
        e_begin, e_end = e['characterOffsetBegin'], e['characterOffsetEnd']
        label = 'O'
        if e_begin in brat_tree:
            node = brat_tree[e_begin]
            if len(node) > 1:
                #print("WARN: multiple starts at ", e_begin, node)
                if e_end in node:
                    #e['ann_id'] = node[e_end][0]  # picking one
                    node = {e_end: node[e_end]}  # picking one
                    #print("Chose:", node)
            ann_end, labels = node.items()[0]
            if not len(labels) == 1:
                print("WARN: Duplicate ids for token: %s, id:%s. Using the first one!" % (e['word'], str(labels)))
            label = labels[0]
            if e_end == ann_end:  # annotation ends where token ends
                continue_ann = None
            elif e_end < ann_end and label != 'O':
                #print("Continue for the next %d chars" % (ann_end - e_end))
                continue_ann = label
                continue_ann_end = ann_end
                continue_ann_begin = e_begin
        elif continue_ann is not None and e_end <= continue_ann_end and e_begin > continue_ann_begin:
            #print("Continuing the annotation %s, %d:%d %d]" % (continue_ann, e_begin, e_end, continue_ann_end))
            label = continue_ann  # previous label is this label
            if continue_ann_end == e_end:  # continuation ends here
                continue_ann = None
        else:
            continue_ann, continue_ann_end, continue_ann_begin = None, None, None
        if label != 'O':
            e['ann_id'] = label

def is_valid_relation_candidate(ner1, ner2, accept_subject2object):
    return ner1 in accept_subject2object and ner2 in accept_subject2object[ner1]

def get_gold_annotid(annfile, accept_ner_labels):
    # only get allowed ner types 
    annotid2position_ner = {}
    annotid2text = {}
    with open(annfile, "r") as f:
        for k in f.readlines():
            k = k.strip()
            if len(k.split("\t")) == 3:
                annot_id, label, span = k.split("\t")
                assert annot_id not in annotid2position_ner

                label, dco_start_char, doc_end_char = label.split()
                dco_start_char = int(dco_start_char)
                doc_end_char = int(doc_end_char)
                if annot_id[0] == "T" and label in accept_ner_labels:
                    annotid2position_ner[annot_id] = (dco_start_char, doc_end_char, label)
                    annotid2text[annot_id] = span.lower()
    return annotid2position_ner, annotid2text

def make_gold_entity_information(annfile, char2sentid, accept_ner_labels, accept_subject2object, no_cross_sentence = True):
    # things to get 
    entitychar2goldlabel = {}
    entity_entity_char2relation = {}
    gold_entity_entity_relation = [] # entity text1, entity text2, relation_label 1 

    annotid2position_ner, annotid2text = get_gold_annotid(annfile, accept_ner_labels)
    entitychar2goldlabel = {(start, end): ner for _, (start, end, ner) in annotid2position_ner.items()}

    entity_entity_relation = []

    # to construct entity_entity_char2relation. this for loop extracts gold relations correctly and could match the statistics. 
    for annotation_line in open(annfile).readlines():
        if annotation_line.strip() == "": continue
        splitline = annotation_line.strip().split('\t')
        annot_id = splitline[0]

        if splitline[0][0] == 'E': # event
            args         = splitline[1].split() 
            relation   = args[0].split(':')[0]
            
            anchor  = args[0].split(':')[1]
            args         = [a.split(':') for a in args[1:]]
            targets = [v for (t,v) in args if t.startswith('Targ')]
            cont    = [v for (t,v) in args if t.startswith('Cont')]

            for t in targets:
                for c in cont:
                    entity_entity_relation.append((t, c, relation))

    for t, c, relation in entity_entity_relation:
        if relation != "Contains": continue
        if t not in annotid2position_ner or c not in annotid2position_ner:
            continue
        type1 = annotid2position_ner[t][-1]
        type2 = annotid2position_ner[c][-1]
        if is_valid_relation_candidate(type1, type2, accept_subject2object):

            # make spans
            doc_start1, doc_end1 = annotid2position_ner[t][:2]
            doc_start2, doc_end2 = annotid2position_ner[c][:2]
            # do not include cross sentence relation 
            if no_cross_sentence:
                sentid1 = None
                for (start, end),sid in char2sentid.items():
                    if start <= doc_start1 < doc_end1 <= end:
                        sentid1 = sid
                sentid2 = None
                for (start, end),sid in char2sentid.items():
                    if start <= doc_start2 < doc_end2 <= end:
                        sentid2 = sid
                assert sentid1 is not None and sentid2 is not None
                if sentid1 != sentid2:
                    continue

            entity_entity_char2relation[(doc_start1, doc_end1, doc_start2, doc_end2)] = relation
            gold_entity_entity_relation.append((annotid2text[t], annotid2text[c], 1))
    return  annotid2position_ner, entitychar2goldlabel, entity_entity_char2relation, gold_entity_entity_relation

def build_eval_set(textfiles, outfile,  corenlp_url, accept_ner_labels, accept_subject2object):

    # Configuration
    corenlp_server = StanfordCoreNLP(corenlp_url)
    props = {'annotators': 'tokenize,ssplit,lemma,pos,ner',
             'ner.model': 'ner_model_train_62r15v3_emt_gazette.ser.gz',
             'outputFormat': 'json'}
   
    gold_entity_entity_relation = [] # for evaluation

    for textfile in textfiles:
        year = re.findall(r"lpsc(\d+)", textfile)[0]
        in_fn = textfile
        ann_fn = textfile.split(".txt")[0] + ".ann"
        fnbase = in_fn.split(".txt")[0].split("/")[-1]
        text, tree = parse(in_fn, ann_fn, accept_ner_labels)

        if text[0].isspace():
            text = '.' + text[1:]
            # Reason: some tools trim/strip off the white spaces
            #  which will mismatch the character offsets

        # Running CoreNLP on Document
        doc = corenlp_server.annotate(text, properties=props)
        # get char2sentid, mainly used to remove cross sentence instances
        char2sentid = {}
        for s in doc['sentences']:
            tokens = [t for t in s['tokens']]
            sentid = int(s["index"]) # starts from 0 
            char2sentid[(tokens[0]["characterOffsetBegin"], tokens[-1]["characterOffsetEnd"])] = sentid


        annotid2position_ner, entitychar2goldlabel, entity_entity_char2relation, entity_entity_relation = make_gold_entity_information(ann_fn,char2sentid, accept_ner_labels, accept_subject2object, no_cross_sentence = True)

        for entity_text1, entity_text2, _ in entity_entity_relation:
            gold_entity_entity_relation.append((year, fnbase, canonical_target_name(entity_text1), canonical_elemin_name(entity_text2)))

    with io.open(outfile, 'w', 
                 encoding='utf8') as outf:
        for year, fnbase, std_entity_text1, std_entity_text2 in sorted(set(gold_entity_entity_relation), key = lambda x: x[1]):  
            to_write = "%s\t%s\t%s\t%s\n"%(year, fnbase, std_entity_text1, std_entity_text2)
            to_write = unicode(to_write, "utf-8")
            outf.write(to_write)
    
# python2 build_tuplebased_eval_testset.py --mode Merged
if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices = ["Element", "Mineral", "Merged"], help = "what experiments to run (e.g., elements, minerals, and their merged set)", required= True)
    args = parser.parse_args()

    # ============ TO MODIFY =============
    mode=args.mode.title() # choices: element, mineral, target
    corenlp_url = "http://localhost:9000"
    datapath = "../data/corpus-LPSC"
    testfiles = glob.glob(join(datapath, "lpsc16-C-raymond-sol1159-utf8/*.txt"))
    outdir = "./eval_testset"
    if not exists(outdir):
    	os.makedirs(outdir)
    outfile = join(outdir, "test.%s.std_eval" % (mode))


    # ====================================
    if mode != "Merged":
        accept_ner_labels = set([
        mode, 
        "Target"])
        
        accept_subject2object = {
            "Target": 
                {mode,}
        }
    else:
        accept_ner_labels = set([
        "Element",
        "Mineral",
        "Target"
        ])
        
        accept_subject2object = {
            "Target": 
                {"Mineral", "Element"}
        }



    # =================== END ==============
    # # ==== make test examples
    build_eval_set(testfiles, outfile, corenlp_url, accept_ner_labels, accept_subject2object)


  