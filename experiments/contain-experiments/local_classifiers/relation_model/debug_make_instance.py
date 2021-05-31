# This function makes within sentence instances and removes duplicates based on texts
import re, pickle, sys, argparse, random, json, os
from sys import stdout 
from os.path import abspath, dirname, join, exists
from os import makedirs, listdir
from transformers import *
curpath = abspath(".")
# curpath = dirname(abspath(__file__))
upperpath = dirname(curpath)
sys.path.append(upperpath)
from instance import Span_Instance, Rel_Instance
from config import label2ind, ind2label, tokenizer_type


parentpath = dirname(upperpath)
sys.path.insert(0, parentpath)
from convertedReader import read_converted, get_docid

tokenizer = BertTokenizerFast.from_pretrained(tokenizer_type)


def make_relation_samples(mode, convfiles,annfiles, outdir, accept_subject2object, use_gold_entities = True, max_len = 512, temp_analysis_dir = "./temp"):

  
    # first collect all valid entity pairs for predictions. this is instance-based, which only relies on character offset 
    extracted_relins = []
    failed_examples = 0 
    collected_relations = []
    for convfile, annfile in zip(convfiles, annfiles):
        venue, year, docname, _ = get_docid(convfile)
        rel_ins,cur_failed_examples = extract_relins_from_converted_file(convfile, accept_subject2object, use_gold_entities = use_gold_entities, max_len = max_len)
       
        for rel in rel_ins:
            print(rel) 
    


def extract_relins_from_converted_file(convfile, accept_subject2object, use_gold_entities = True, max_len = 512):
    

    rel_ins = []

    venue, year, docname, _ = get_docid(convfile)

    doc = read_converted(convfile)

    entities = doc["predicted_entities"] if not use_gold_entities else doc["gold_entities"]

    # entities is a list of list, each list is a sentence. here we take only entity pairs from the same sentence
    failed_examples = 0
    for sentence_entities in entities:
        sentid = sentence_entities[0]["sentid"]
        sent_toks = doc["sents"][sentid]


        for i in range(len(sentence_entities)):
            entity1 = sentence_entities[i]
            ner1 = entity1["predicted_ner"] if not use_gold_entities else entity1["gold_ner"]

            
            span1 = Span_Instance(venue, year, docname, entity1["doc_start_char"], entity1["doc_end_char"],  entity1["text"].lower(), ner1, sent_toks = sent_toks,  sentid = entity1["sentid"], sent_start_idx =entity1["sent_start_idx"], sent_end_idx = entity1["sent_end_idx"])

           


            
            if ner1 not in accept_subject2object:
                continue

            for j in range(len(sentence_entities)):
                if j == i: continue
                entity2 = sentence_entities[j]

                ner2 = entity2["predicted_ner"] if not use_gold_entities else entity2["gold_ner"]

                
                if ner2 not in accept_subject2object[ner1]:
                    continue

                span2 = Span_Instance(venue, year, docname, entity2["doc_start_char"], entity2["doc_end_char"],  entity2["text"].lower(), ner2, sent_toks = sent_toks,  sentid = entity2["sentid"], sent_start_idx =entity2["sent_start_idx"], sent_end_idx = entity2["sent_end_idx"])
                
                rel = Rel_Instance(span1, span2)
                # insert type markers into input ids around two entities. The returned value identifies if the inserting is successful
                success = rel.insert_type_markers(tokenizer, max_len = max_len)

                if success:
                    rel_ins.append(rel)
                else:
                    failed_examples += 1




    return rel_ins, failed_examples

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

def make_gold_relins(annfiles, convfiles, accept_subject2object):
    # convfile is used to check if the relations cross sentences

    print("WARNING: only use and evaluate with the relations not crossing sentences")

    gold_relins = [] # this doesn't count cross sentence instance. Instance level 

    for filenum, (annfile, convfile) in enumerate(zip(annfiles, convfiles)):


        # currently this functions is tested only over lpsc, mpf and phx dataset 
        assert "mpf" in annfile.lower() or "phx" in annfile.lower() or "lpsc" in annfile.lower()
        is_mpfphx = "mpf" in annfile.lower() or "phx" in annfile.lower() # phx and mpf use different representation in ann file than lpsc documents. So we need different ways handling them.
        
        venue, year, docname, _ = get_docid(convfile)
        doc = read_converted(convfile)

        entity_entity_relation = []

        annotid2position_ner, annotid2text = get_gold_annotid(annfile)

        annotid_annotid_relation = []
        all_instances = set() # includes cross sentence and within sentence instances

        # this for loop extracts gold relations correctly and could match the statistics
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
            type1 = annotid2position_ner[t][-1]
            type2 = annotid2position_ner[c][-1]
            if type1 in accept_subject2object and type2 in accept_subject2object[type1] and relation == "Contains": 
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

                if sentid1 != sentid2:
                    continue

                span1 = Span_Instance(venue, year, docname, doc_start1, doc_end1,  ttext, type1, sentid = sentid1)
                span2 = Span_Instance(venue, year, docname, doc_start2, doc_end2,  ctext, type2, sentid = sentid2)

                rel = Rel_Instance(span1, span2, label_str = relation)

                gold_relins.append(rel)

    print(f"collect {len(gold_relins)} instance-level gold relations ")
   
    return gold_relins


def add_mpfphx(test_convfiles, test_annfiles):
        convertedmpf_indir = join(dirname(parentpath), "data/converted/corpus-LPSC-with-ner/mpf-reviewed+properties-v2")
        annmpf_indir = join(dirname(parentpath), "data/corpus-LPSC/mpf-reviewed+properties-v2")
        test_convfiles += [join(convertedmpf_indir, file) for file in listdir(convertedmpf_indir) if file.endswith(".txt")]
        test_annfiles += [join(annmpf_indir, file.split(".txt")[0] + ".ann") for file in listdir(convertedmpf_indir) if file.endswith(".txt")]

        convertedphx_indir = join(dirname(parentpath), "data/converted/corpus-LPSC-with-ner/phx-reviewed+properties")
        annphx_indir = join(dirname(parentpath), "data/corpus-LPSC/phx-reviewed+properties")
        test_convfiles += [join(convertedphx_indir, file) for file in listdir(convertedphx_indir) if file.endswith(".txt")]
        test_annfiles += [join(annphx_indir, file.split(".txt")[0] + ".ann") for file in listdir(convertedphx_indir) if file.endswith(".txt")]
        return test_convfiles, test_annfiles


accept_subject2object = {
            "Target":
                {"Element", "Mineral"}
        }
# =======================================
test_convfiles, test_annfiles = add_mpfphx([], [])

convfiles = ["../../../data/converted/corpus-LPSC-with-ner/mpf-reviewed+properties-v2/1998_1534.txt"]
annfiles = ["../../../data/corpus-LPSC/mpf-reviewed+properties-v2/1998_1534.ann"]

use_gold_entities = True, max_len = 512
make_relation_samples("Merged", convfiles, annfiles, "", accept_subject2object, use_gold_entities = True, max_len = 512)

