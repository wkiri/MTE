# This function makes within sentence instances and removes duplicates based on texts
import re, pickle, sys, argparse, random, json, os
from sys import stdout 
from os.path import abspath, dirname, join, exists
from os import makedirs, listdir

curpath = dirname(abspath(__file__))
upperpath = dirname(curpath)
sys.path.append(upperpath)
from instance import Span_Instance


from config import label2ind, ind2label,  tokenizer_type

parentpath = dirname(dirname(curpath))
sys.path.insert(0, parentpath)
from convertedReader import read_converted, get_docid

from transformers import *
tokenizer = BertTokenizerFast.from_pretrained(tokenizer_type)

def make_instances(mode, convfiles,annfiles, outdir, accept_ner_types, use_gold_entities = True, max_len = 512):

    # first collect all valid entity for predictions. this is instance-based, which only relies on character offset. extract spans that cooccur with target in a sentence
    extracted_spanins = []
    for convfile, annfile in zip(convfiles, annfiles):
        span_ins = extract_spanins_from_converted_file(mode, convfile,accept_ner_types, use_gold_entities = use_gold_entities, max_len = max_len)
        # load relation id 2 relation label from annfile

        extracted_spanins.extend(span_ins)


    # load annoatated spans. gold_spanins: spans that are involved in contain relations. this is for instance-level evaluation. 
    # gold_cross_spanins: spans that are only involved in cross-sentence contain relations

    # gold_spanins, cross_gold_spanins = make_gold_spanins_instances(annfiles, convfiles, accept_ner_types)

    # extract spans that are involved in in-sentence relations
    gold_spanins = make_gold_spanins_instances(annfiles, convfiles, accept_ner_types)
    print(f"In total {len(gold_spanins)} gold spans involved in contain relations in annotations ")

    # make a mapping fom relation id to relation, in order to assign the gold relation label to all relation instances in extracted_rel_ins 
    gold_spanid = set([ins.span_id for ins in gold_spanins])
    # cross_gold_spanid = set([ins.span_id for ins in cross_gold_spanins])
    extracted_spanid = set([ins.span_id for ins in extracted_spanins])

    found = len(extracted_spanid.intersection(gold_spanid))
    print(f"{found}/{len(gold_spanins)}({found/len(gold_spanid)}) gold annotations are found in the extracted instances")


    # assign relation label to rel instance according to annfile and relation_id.
    for i in range(len(extracted_spanins)):
        spanid = extracted_spanins[i].span_id
        if spanid in gold_spanid:
            relation_label = "Contains"
        else:
            relation_label = "O"

        extracted_spanins[i].relation_label = relation_label
   

    if not exists(outdir):
        os.makedirs(outdir)

    # with open(join(outdir, f"{mode}.extract_instances.contain.txt"), "w") as f: 
    #     for ins in sorted(extracted_spanins, key = lambda x: (x.doc_id, x.sentid)):
    #         if ins.relation_label != "O":
    #             f.write(f"DOC: {ins.doc_id}\nSENT({ins.sentid}): {' '.join(ins.sent_toks)}\nTEXT: {ins.text}\nRELLABEL: {ins.relation_label}\n\n")

    # with open(join(outdir, f"{mode}.extract_instances.O.txt"), "w") as f: 
    #     for ins in sorted(extracted_spanins, key = lambda x: (x.doc_id, x.sentid)):
    #         if ins.relation_label == "O":
    #             f.write(f"DOC: {ins.doc_id}\nSENT({ins.sentid}): {' '.join(ins.sent_toks)}\nTEXT: {ins.text}\nRELLABEL: {ins.relation_label}\n\n")

    # with open(join(outdir, f"{mode}.eval_instances.contain.txt"), "w") as f: 
    #     for ins in sorted(gold_spanins, key = lambda x: (x.doc_id, x.sentid)):
    #         if ins.relation_label != "O":
    #             f.write(f"DOC: {ins.doc_id}\nSENTID:{ins.sentid}\nTEXT: {ins.text}\nRELLABEL: {ins.relation_label}\n\n")

    # with open(join(outdir, f"{mode}.eval_instances.contain.txt"), "w") as f: 
    #     for ins in sorted(gold_spanins, key = lambda x: (x.doc_id, x.sentid)):
    #         if ins.relation_label == "O":
    #             f.write(f"DOC: {ins.doc_id}\nSENTID:{ins.sentid}\nTEXT: {ins.text}\nRELLABEL: {ins.relation_label}\n\n")




    num_pos = sum([1 for ins in extracted_spanins if ins.relation_label != 'O'])
    num_neg = sum([1 for ins in extracted_spanins if ins.relation_label == 'O'])
    print(f"In total {num_pos + num_neg} instances extracted, with {num_pos} positive and {num_neg} negative . ")

    if not exists(outdir):
        os.makedirs(outdir)
    outfile = join(outdir, f"{mode}.extracted_{'gold' if use_gold_entities else 'system'}_spanins.pkl")
    print(f"saving to {outfile}")
    with open(outfile, "wb") as f:
        pickle.dump(extracted_spanins, f)

    outfile = join(outdir, f"{mode}.annotated_gold_spanins.pkl")
    print(f"saving the evaluation set to {outfile}")
    with open(outfile, "wb") as f:
        pickle.dump(gold_spanins, f)

    print()

    return extracted_spanins


def extract_spanins_from_converted_file(mode, convfile, accept_ner_types, use_gold_entities = True, max_len = 512):


    
    venue, year, docname, _ = get_docid(convfile)

    doc = read_converted(convfile)

    entities = doc["predicted_entities"] if not use_gold_entities else doc["gold_entities"]

    span_ins = []

    # IMPORTANT: NOTE THAT we only take candidates from sentences where a pair of target/element or target/mineral exists. If a sentence contains only an element, that element wouldn't be taken as candidate. This is to reduce the number of negative samples, and also make it a fair comparison to the relation model that uses positive/negative relations from sentence that contains at least one target/element or target/mineral. FURTHERMORE, if the element/mineral is only involved in cross relation, we don't take it as a candidate 
    for sentence_entities in entities:

        sentid = sentence_entities[0]["sentid"]
        sent_toks = doc["sents"][sentid]

        sent_ners = set([entity["predicted_ner"] if not use_gold_entities else entity["gold_ner"] for entity in sentence_entities])


        
        if mode == "Merged":
            # needs to have target, element/mineral
           
            if "Target" not in sent_ners or  ("Element" not in sent_ners and "Mineral" not in sent_ners): 
                continue
        else:
            if "Target" not in sent_ners:
                continue
            should_stop = 1
            if mode == "T":
                should_stop = "Element" not in sent_ners and "Mineral" not in sent_ners
            else:
                for c in mode: 
                    if d[c] in sent_ners:
                        should_stop = 0
                        break
            if should_stop:
                continue





        for i in range(len(sentence_entities)):
            entity1 = sentence_entities[i]
            ner1 = entity1["predicted_ner"] if not use_gold_entities else entity1["gold_ner"]

            span1 = Span_Instance(venue, year, docname, entity1["doc_start_char"], entity1["doc_end_char"],  entity1["text"].lower(), ner1, sent_toks = sent_toks,  sentid = entity1["sentid"], sent_start_idx =entity1["sent_start_idx"], sent_end_idx = entity1["sent_end_idx"]) 

            if ner1 not in accept_ner_types:
                continue

            if span1.insert_type_markers(tokenizer,use_std_text = True, max_len = max_len):
                
                span_ins.append(span1)

    unique_span_ins = []
    seen_id = set()
    for ins in span_ins:
        if ins.span_id in seen_id:
            continue
        unique_span_ins.append(ins)
        seen_id.add(ins.span_id)


    return unique_span_ins



            


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
                if annot_id[0] == "T":
                    annotid2position_ner[annot_id] = (doc_start_char, doc_end_char, label)
                    annotid2text[annot_id] = span.lower()
    return annotid2position_ner, annotid2text

def make_gold_spanins_instances(annfiles, convfiles, accept_ner_types):
    # convfile is used to check if the relations cross sentences

    print("WARNING: only use and evaluate with the relations not crossing sentences")

    gold_span_ins = [] # this includes spans that cooccur with target in the same sentence and has the contain relations
    all_gold_spanins = [] # use to identify cross-sentence instances

    # tot_entity_entity_relations = []
    for filenum, (annfile, convfile) in enumerate(zip(annfiles, convfiles)):
        # currently this functions is tested only over lpsc, mpf and phx dataset 

        assert "mpf" in annfile.lower() or "phx" in annfile.lower() or "lpsc" in annfile.lower()
        is_mpfphx = "mpf" in annfile.lower() or "phx" in annfile.lower() # phx and mpf use different representation in ann file than lpsc documents. So we need different ways handling them. 


        doc = read_converted(convfile)
        venue, year, docname, _ = get_docid(convfile)

        entity_entity_relation = []

        annotid2position_ner, annotid2text = get_gold_annotid(annfile) 

        annotid_annotid_relation = []
        all_instances = set() # includes cross sentence and within sentence instances

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
            # tot_entity_entity_relations.extend(entity_entity_relation)
            # now apply filtering and collect gold relations
            # print(entity_entity_relation)

        for t, c, relation in entity_entity_relation:

            type1 = annotid2position_ner[t][-1]
            type2 = annotid2position_ner[c][-1]


            if  relation == "Contains":
                doc_start1, doc_end1 = annotid2position_ner[t][:2]
                doc_start2, doc_end2 = annotid2position_ner[c][:2]
                ttext = annotid2text[t]
                ctext = annotid2text[c]
                
                sentid1 = -1 
                for bound in doc["char2sentid"]:
                    if bound[0] <= doc_start1 < bound[1]:
                        sentid1 = doc["char2sentid"][bound]
                        break
                assert sentid1 != -1

                sentid2 = -1 
                for bound in doc["char2sentid"]:
                    if bound[0] <= doc_start2 < bound[1]:
                        sentid2 = doc["char2sentid"][bound]
                        break
                assert sentid2 != -1

                
                if type1 in accept_ner_types:
                    span1 = Span_Instance(venue, year, docname, doc_start1, doc_end1,  ttext, type1, sentid = sentid1)
                    span1.relation_label = "Contains"
                    if sentid1 == sentid2: 
                        gold_span_ins.append(span1)

                    all_gold_spanins.append(span1)


                if type2 in accept_ner_types:
                    span2 = Span_Instance(venue, year, docname, doc_start2, doc_end2, ctext, type2, sentid = sentid2)
                    span2.relation_label = "Contains"
                    
                    if sentid1 == sentid2: 
                        gold_span_ins.append(span2)

                    all_gold_spanins.append(span2)
    

    # remove duplicated span ins as a span ins could be involved in several contain relations
    seen_spanid = set()
    new_gold_span_ins = []
    for ins in gold_span_ins:
        if ins.span_id in seen_spanid:
            continue
        new_gold_span_ins.append(ins)
        seen_spanid.add(ins.span_id)

    # new_cross_span_ins = [] # this stores instances that are involved in only cross-sentence relations

    # for ins in all_gold_spanins:
    #     if ins.span_id in seen_spanid:
    #         continue
    #     new_cross_span_ins.append(ins)
    #     seen_spanid.add(ins.span_id)
   
    # return new_gold_span_ins, new_cross_span_ins

    return new_gold_span_ins
# python make_train_val_test.py > ./stat/train_dev_test.txt
if __name__ == "__main__":
    # make training/val/test instances, and gold spans

    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices = ["Merged", "EM", "ET", "MT", "E", "M", "T"], help = "what experiments to run (e.g., elements, minerals, and their merged set)", required= True)

    args = parser.parse_args()

    # =============================
    mode = args.mode
    if mode == "Merged":
        accept_ner_types = set(["Element", "Mineral", "Target"])
    else:
        accept_ner_types = set()
        d = {
        "E": "Element", 
        "M": "Mineral",
        "T": "Target"}

        for c in mode:
            accept_ner_types.add(d[c])





    # ---- make training samples ----
    outdir = join(curpath, "ins")

    converted15_indir = join(dirname(parentpath), "data/converted/corpus-LPSC-with-ner/lpsc15")
    ann15_indir = join(dirname(parentpath), "data/corpus-LPSC/lpsc15")

    train_convfiles = [join(converted15_indir, file.split(".ann")[0] + ".txt") for file in listdir(ann15_indir) if file.endswith(".ann")][:42]
    train_annfiles = [join(ann15_indir, file) for file in listdir(ann15_indir) if file.endswith(".ann")][:42]

    val_convfiles = [join(converted15_indir, file.split(".ann")[0] + ".txt") for file in listdir(ann15_indir) if file.endswith(".ann")][42:]
    val_annfiles = [join(ann15_indir, file) for file in listdir(ann15_indir) if file.endswith(".ann")][42:]

    converted16_indir = join(dirname(parentpath), "data/converted/corpus-LPSC-with-ner/lpsc16")
    ann16_indir = join(dirname(parentpath), "data/corpus-LPSC/lpsc16")

    
    test_convfiles = [join(converted16_indir, file.split(".ann")[0] + ".txt") for file in listdir(ann16_indir) if file.endswith(".ann")]

    test_annfiles = [join(ann16_indir, file) for file in listdir(ann16_indir) if file.endswith(".ann")]

    print(" ----- making training samples ... ")
    train_outdir = join(outdir, "train")
    make_instances(mode, train_convfiles,train_annfiles, train_outdir, accept_ner_types, use_gold_entities = True)



    # ---- make val samples ----
    print(" ----- making val samples ... ")
    val_outdir = join(outdir, "val")
    make_instances(mode,val_convfiles, val_annfiles, val_outdir, accept_ner_types, use_gold_entities = True)



    # -------- make test samples ---------
    print(" ----- making test samples ... ")
    test_outdir = join(outdir,"test")
    make_instances(mode, test_convfiles, test_annfiles, test_outdir, accept_ner_types, use_gold_entities = True, max_len = 512)

    make_instances(mode, test_convfiles, test_annfiles, test_outdir, accept_ner_types, use_gold_entities = False, max_len = 512)



