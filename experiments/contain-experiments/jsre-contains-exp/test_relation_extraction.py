# This code produces word-word pair training/val/test examples for jSRE model. 
# This code requires python2.
# Before running this code, go to MILA and activate the virtualenv at /home/yzhuang/env. Run a StanfordCoreNLP server. Also need to modify config.py to constraint the relation and types of ners 

import sys, os, io, json, argparse, glob, re, ast
# The following two lines make CoreNLP happy
reload(sys)
from sys import stdout 
sys.setdefaultencoding('UTF8')
from pycorenlp import StanfordCoreNLP
from os.path import abspath, dirname, join
curpath = abspath(".")
# curpath = dirname(abspath(__file__))
parentpath = dirname(curpath)
sys.path.append(parentpath)
from my_name_utils import canonical_target_name, canonical_elemin_name

def parse(txt_file, annfile, accept_entities):
    with open(txt_file) as textfile, open(annfile) as annfile:
        texts = textfile.read().decode('utf8')
        textfile.close()
        anns = map(lambda x: x.strip().split('\t'), annfile)
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
        textfile = open(txt_file)
        texts = textfile.read()
        textfile.close()
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

def generate_example_id(year, fnbase, char_start_end1, char_start_end2, tok_idx1, tok_idx2, sentid, org_text1, org_text2, entity_ner_label1, entity_ner_label2, org_before_text1, org_before_text2):
    # Create a unique identifier that contains enough information such that we could reconstruct entity-level examples from the id 
    return json.dumps([year,fnbase,char_start_end1, char_start_end2, tok_idx1, tok_idx2, sentid, org_text1, org_text2, entity_ner_label1, entity_ner_label2, org_before_text1, org_before_text2])


def generate_example(id, label, sentence, target_index, active_index, target_gold_ner, active_gold_ner):
    body = ''
    for t in sentence['tokens']:
        # Target entity is the agent;
        # Element entity is the target (of the relation)
        if t['index'] == target_index:
            entity_label = 'A'
            gold_ner = target_gold_ner
        elif t['index'] == active_index:
            entity_label = 'T'
            gold_ner = active_gold_ner
        else:
            entity_label = 'O'
            gold_ner = "O"

        # CoreNLP indexes starting at 1
        body += '%d&&%s&&%s&&%s&&%s&&%s ' % (t['index'] - 1,
                                             t['word'],
                                             t['lemma'],
                                             t['pos'],
                                             # t['ner'],
                                             gold_ner,
                                             entity_label)
    # Output the example
    example = '%s\t%s\t%s\n' % (label, id, body)
    return example


def assign_training_label(tok_char_start1, tok_char_start2, entitychar2goldlabel, entity_entity_char2relation, relation_to_assign):
    # see if the target word and active word is in the annotation file. 
    # a positive label is assigned if: 
    #     1. target word is in an entity that is a valid subject, 
    #     2. active word is in an entity that is a valid object of that subject, 
    #     3. entity1 and entity2 exists in annotation file
   
    # find entity char position of tok1 and tok2 first
    def find_entity_char(tokchar):
        for start, end in entitychar2goldlabel:
            if start <= tokchar < end:
                return start, end 
        return -1, -1 

    entity_start_char1, entity_end_char1 = find_entity_char(tok_char_start1)
    entity_start_char2, entity_end_char2 = find_entity_char(tok_char_start2)

    entity_ner_label1 = entitychar2goldlabel.get((entity_start_char1, entity_end_char1), "O")
    entity_ner_label2 = entitychar2goldlabel.get((entity_start_char2, entity_end_char2), "O")

    if entity_ner_label1 in accept_subject2object:
        if entity_ner_label2 in accept_subject2object[entity_ner_label1]:
            if entity_entity_char2relation.get((entity_start_char1, entity_end_char1, entity_start_char2, entity_end_char2), None) == relation_to_assign:
                return 1, entity_ner_label1, entity_ner_label2
    return 0, entity_ner_label1, entity_ner_label2

def keep_example(target, active, annotid2position_ner, use_gold_entities):

    # NOTE THAT this condition doesn't generate the same list of examples as the word-word pair jSRE model in the IAAI paper, where only examples that are predicted to be NER entities and exist in annotation are kept. 

    # if use_gold_entities, example kept only if target and active are 1. both ner entities in annotation, 2. (target, active) is a valid candidate for a relation e.g. Contains. this is checked by finding if target is in accept_subject2object and active is in accept_subject2object[target].

    if use_gold_entities:
        if "ann_id" not in target or "ann_id" not in active:
            return False

        type1 = annotid2position_ner[target["ann_id"]][-1]
        type2 = annotid2position_ner[active["ann_id"]][-1]
        if type1 not in accept_subject2object or type2 not in accept_subject2object[type1]:
            return False
        return True
    else:
        # otherwise use system entities. this is exactly the same as the last if, except that target and active should be both ner entities predicted by the ner model
        if target["ner"] not in accept_subject2object or active['ner'] not in accept_subject2object[target['ner']]:
            return False
        return True 




def is_valid_relation_candidate(ner1, ner2):
    return ner1 in accept_subject2object and ner2 in accept_subject2object[ner1]

def get_gold_annotid(annfile):
    # only get allowed ner types 
    annotid2position_ner = {}
    annotid2text = {}
    with open(annfile, "r") as f:
        for k in f.readlines():
            k = k.strip()

            if len(k.split("\t")) == 3:
                annot_id, label, span = k.split("\t")
                assert annot_id not in annotid2position_ner

                label, doc_start_char, doc_end_char = label.split()
                doc_start_char = int(doc_start_char)
                doc_end_char = int(doc_end_char)
                if annot_id[0] == "T" and label in accept_ner_labels:
                    annotid2position_ner[annot_id] = (doc_start_char, doc_end_char, label)
                    annotid2text[annot_id] = span.lower()

    return annotid2position_ner, annotid2text

# changed 
def make_gold_entity_information(annfile, relation_to_assign, char2sentid, no_cross_sentence = True):
    # currently this functions is tested only over lpsc, mpf and phx dataset 
    assert "mpf" in annfile.lower() or "phx" in annfile.lower() or "lpsc" in annfile.lower()
    is_mpfphx = "mpf" in annfile.lower() or "phx" in annfile.lower() # phx and mpf use different representation in ann file than lpsc documents. So we need different ways handling them. 

    # things to get 
    entitychar2goldlabel = {}
    entity_entity_char2relation = {}
    gold_entity_entity_relation = [] # entity text1, entity text2, relation_label 1 

    annotid2position_ner, annotid2text = get_gold_annotid(annfile)
    entitychar2goldlabel = {(start, end): ner for _, (start, end, ner) in annotid2position_ner.items()}

    entity_entity_relation = []

    # to construct entity_entity_char2relation. this for loop extracts gold relations correctly and could match the statistics. 
    for annotation_line in open(annfile).readlines():
        if annotation_line.strip() == "": continue
        splitline = annotation_line.strip().split('\t')
        annot_id = splitline[0]

        if is_mpfphx:
            if splitline[0][0] == "R":
                args = splitline[1].split()
                if len(args) == 3:
                    relation = args[0]
                    arg1 = args[1].split(":")[1]
                    arg2 = args[2].split(":")[1]
                    entity_entity_relation.append((arg1, arg2, relation))
        else:
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
        if relation != relation_to_assign: continue
        if t not in annotid2position_ner or c not in annotid2position_ner:
            continue
        type1 = annotid2position_ner[t][-1]
        type2 = annotid2position_ner[c][-1]
        if is_valid_relation_candidate(type1, type2):
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

def build_jsre_examples(mode, relation_to_assign,textfiles, out_path,  corenlp_url, use_gold_entities):
    """
    Build jSRE examples from CoreNLP NER and Brat Annotations
    :param relation_to_assign: relation to extract
    :param in_path: path to the input directory
    :param out_path: path to the output directory
    :param corenlp_url: URL of Stanford CoreNLP Server
    """

    # Configuration
    corenlp_server = StanfordCoreNLP(corenlp_url)
    props = {'annotators': 'tokenize,ssplit,lemma,pos,ner',
             'ner.model': 'ner_model_train_62r15v3_emt_gazette.ser.gz',
             'outputFormat': 'json'}

    if not os.path.exists(out_path):
        print 'Creating output directory %s' % out_path
        os.makedirs(out_path)

    # Select *.txt files
    print 'Processing %d documents. ' % len(textfiles)
    examples = []
    count_examples = {0:0, 1:0}
   
    gold_entity_entity_relation = [] # for evaluation
    out_eval_fn = join(out_path, "%s.std_eval" % (mode))
    out_wordword_file = join(out_path, "%s.wword_instance" % (mode))
    wordword_instances = []

    for numfile, textfile in enumerate(textfiles):
        stdout.write("processing %s/%s documents. Generated word-word examples, including %s positive and %s negative\r" % (str(numfile), str(len(textfiles)), count_examples[1], count_examples[0]))
        stdout.flush()

        try: # works for lpsc15 and 16 
            year = re.findall(r"lpsc(\d+)", textfile)[0]
            fnbase = textfile.split(".txt")[0].split("/")[-1]

        except:
            year, fnbase = re.findall(r"(\d+)_(\d+)", textfile.split("/")[-1])[0]
        ann_fn = textfile.split(".txt")[0] + ".ann"

        out_fn = '%s-%s.examples' % (fnbase, relation_to_assign.lower())

        accept_entities = set(accept_ner_labels)
        text, tree = parse(textfile, ann_fn, accept_entities)

        if text[0].isspace():
            text = '.' + text[1:]
            # Reason: some tools trim/strip off the white spaces
            #  which will mismatch the character offsets

        # Running CoreNLP on Document
        doc = corenlp_server.annotate(text, properties=props)
        if type(doc) == type({}):
            pass
        elif type(doc) == type("") or  type(doc) == type(u""):
           doc = ast.literal_eval(doc)
        else:
            raise NameError("weird type of result returned from corenlp: %s, file = %s "%(type(doc), textfile))

        # get char2sentid, mainly used to remove cross sentence instances
        char2sentid = {}
        for s in doc['sentences']:
            tokens = [t for t in s['tokens']]
            sentid = int(s["index"]) # starts from 0 
            char2sentid[(tokens[0]["characterOffsetBegin"], tokens[-1]["characterOffsetEnd"])] = sentid


        annotid2position_ner, entitychar2goldlabel, entity_entity_char2relation, entity_entity_relation = make_gold_entity_information(ann_fn, relation_to_assign, char2sentid, no_cross_sentence = True)

        for entity_text1, entity_text2, _ in entity_entity_relation:
            gold_entity_entity_relation.append((year, fnbase, canonical_target_name(entity_text1), canonical_elemin_name(entity_text2)))


        with io.open(os.path.join(out_path, out_fn), 'w', 
                     encoding='utf8') as outf:
            # Map Raymond's .ann (brat) annotations into the CoreNLP-parsed
            # sentence/token structure.

            # this generates only in-sentence examples 
            examples = []

           
            for s in doc['sentences']:

                tokens = [t for t in s['tokens']]
                sentid = int(s["index"]) # starts from 0 

                include_brat_ann(tokens, tree)
                for i in range(len(tokens)):

                    for j in range(len(tokens)):
                        if i == j: continue
                        target = tokens[i]
                        active = tokens[j]
                        if keep_example(target, active, annotid2position_ner,use_gold_entities):

                            # doc_examples.append((targets[i], active[j]))
                            char_start_end1 = (target["characterOffsetBegin"], target["characterOffsetEnd"])
                            char_start_end2 = (active["characterOffsetBegin"], active["characterOffsetEnd"])
                            tok_idx1 = target["index"] - 1
                            tok_idx2 = active["index"] - 1

                            org_text1 = target["originalText"]
                            org_text2 = active["originalText"]

                            # this is used to aggregate entities later. mainly it is used to identify if two tokens are separated by hyphens 
                            org_before_text1 = tokens[i-1]["originalText"] if i-1 >=0 else None
                            org_before_text2 = tokens[j-1]["originalText"] if j-1 >= 0 else None

                            # this label is mainly used for training examples
                            label, entity_ner_label1, entity_ner_label2 = assign_training_label(char_start_end1[0], char_start_end2[0],  entitychar2goldlabel, entity_entity_char2relation, relation_to_assign)
                            
                            id = generate_example_id(year, fnbase, char_start_end1, char_start_end2, tok_idx1, tok_idx2, sentid, org_text1, org_text2, entity_ner_label1, entity_ner_label2, org_before_text1, org_before_text2)

                            example = generate_example(id, label, s, 
                                                       target['index'], 
                                                   active['index'], entity_ner_label1, entity_ner_label2)
                            wordword_instances.append((year, fnbase, org_text1, org_text2))
                            outf.write(example)
                            count_examples[label] += 1
        
    with io.open(out_eval_fn, 'w', 
                 encoding='utf8') as outf:
        for year, fnbase, std_entity_text1, std_entity_text2 in sorted(set(gold_entity_entity_relation), key = lambda x: x[1]):  
            to_write = "%s\t%s\t%s\t%s\n"%(year, fnbase, std_entity_text1, std_entity_text2)
            to_write = unicode(to_write, "utf-8")
            outf.write(to_write)
    with io.open(out_wordword_file, "w", encoding = "utf8") as outf:
        for year, fnbase, text1, text2 in sorted(set(wordword_instances), key = lambda x: x[1]):
            to_write = "%s\t%s\t%s\t%s\n"%(year, fnbase, text1, text2)
            outf.write(to_write)

    print("Generated word-word examples, including %s positive and %s negative" % (count_examples[1], count_examples[0]))

# python2 generate_jsre_binary_relation_examples.py --mode Merged; python2 generate_jsre_binary_relation_examples.py --mode Element; python2 generate_jsre_binary_relation_examples.py --mode Mineral
if __name__ == '__main__':

   

    # ============ TO MODIFY =============
    mode = "Merged"
    out_path = "./temp"
    corenlp_url = "http://localhost:9000"
    datapath = "../../data/corpus-LPSC"
    testfiles = glob.glob(join(datapath, "mpf-reviewed+properties-v2/*_*.txt")) + glob.glob(join(datapath, "phx-reviewed+properties/*_*.txt"))

    accept_ner_labels = [
    "Element",
    "Mineral",
    "Target"
    ]
        
    accept_subject2object = {
            "Target": 
                {"Mineral", "Element"}
        }

    relation_to_assign = "Contains"


    # find the files that contains "contains" relation annotation 
    contains_textfiles = []
    for file in testfiles:
        annfile = file.split(".txt")[0] + ".ann"
        with open(annfile, "r") as f:
            text = f.read()
            if re.search(r"Contains", text):
                contains_textfiles.append(file)
    testfiles = contains_textfiles
    # # e.g. 
    # testfiles = ['../../data/corpus-LPSC/mpf-reviewed+properties-v2/1999_1912.txt']

    # =================== END ==============
    # # ==== make test examples
    use_gold_entities = 1 # use gold entities to predict relations
    out_path = join(outdir, "test-goldentity")
    build_jsre_examples(mode, relation_to_assign, testfiles, out_path,  corenlp_url, use_gold_entities)
    