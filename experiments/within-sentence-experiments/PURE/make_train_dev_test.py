# python3
# make_train_dev_test.py
# Mars Target Encyclopedia
# This script makes within-sentence containee examples for training, development and test set.
#
# Yuan Zhuang
# July 30, 2021
# Copyright notice at bottom of file.

# author: Yuan Zhuang 
# This code make train, dev and test set in a format that PURE takes. 
import re, pickle, sys, argparse, random, json, os
from copy import deepcopy 
from sys import stdout 
from os.path import abspath, dirname, join, exists
from os import makedirs, listdir
from transformers import *

curpath = dirname(abspath(__file__))
shared_path = join(dirname(dirname(curpath)), "shared")
sys.path.append(shared_path)
from instance import Span_Instance, Rel_Instance

from extraction_utils import get_docid, extract_gold_entities_from_ann,extract_intrasent_entitypairs_from_text_file, extract_intrasent_goldrelations_from_ann, extract_entities_from_text, get_offset2sentid, get_sentid_from_offset

from other_utils import read_inlist




def extract_data_for_pure(ann_file, text_file, cornelp_file,  use_component, max_len = 512, use_sys_ners = False):

    accept_ner2 = ['Component'] if use_component else ['Element', 'Mineral']

    venue, year, docname, _ = get_docid(text_file)

    doc = json.load(open(cornelp_file, 'r'))

    # gold relations are used to assign training label for training instances, and nothing else. 
    intrasent_gold_relations = [ (e1, e2, relation) for e1, e2, relation in extract_intrasent_goldrelations_from_ann(ann_file, doc = doc, use_component = use_component) if relation == 'Contains' and e1['label'] == 'Target' and e2['label'] in accept_ner2]
    
    gold_relation_ids = set([f"{e1['venue']},{e1['year']},{e1['docname']},{e1['doc_start_char']},{e1['doc_end_char']},{e2['doc_start_char']},{e2['doc_end_char']}" for e1, e2, relation in intrasent_gold_relations])


    ret_doc = {"ner": [], 
    "sentences": [ [token['word'] for token in sent['tokens']] for sent in doc["sentences"]], 
    "doc_key": f"{venue},{year},{docname}",
    "relations": [],
    } 
    ret_doc["ner"] = [[] for _ in ret_doc['sentences']]
    ret_doc["relations"] = [[] for _ in ret_doc['sentences']]

    # group entities by sentence id.
    for e1, e2 in extract_intrasent_entitypairs_from_text_file(text_file, ann_file, doc = doc, use_component = use_component, use_sys_ners = use_sys_ners):
        sentid = e1['sentid']

        sent_toks = ret_doc['sentences'][sentid]
        cum_toks = sum([len(ret_doc["sentences"][i]) for i in range(sentid)])


        ner1 = e1["label"]

        if ner1 not in ['Target'] + accept_ner2:
            continue
        
        span1_doc_start_char = e1["doc_start_char"]
        span1_doc_end_char = e1["doc_end_char"]

        span1 = [e1["sent_start_idx"] + cum_toks, e1["sent_end_idx"] - 1 + cum_toks, ner1]

        
        if tuple(span1) not in set([tuple(s) for s in ret_doc['ner'][sentid]]):

            ret_doc["ner"][sentid].append(span1)


        ner2 = e2['label']
        if ner1 != 'Target' or ner2 not in accept_ner2:
            continue

        span2_doc_start_char = e2["doc_start_char"]
        span2_doc_end_char = e2["doc_end_char"]

        span2 = [e2["sent_start_idx"] + cum_toks,e2["sent_end_idx"] - 1 + cum_toks, ner2]

        if tuple(span2) not in set([tuple(s) for s in ret_doc['ner'][sentid]]):
            ret_doc["ner"][sentid].append(span2)

        if f"{e1['venue']},{e1['year']},{e1['docname']},{e1['doc_start_char']},{e1['doc_end_char']},{e2['doc_start_char']},{e2['doc_end_char']}" in gold_relation_ids:

            ret_doc['relations'][sentid].append([span1[0], span1[1], span2[0], span2[1], 'Contains'])
            
    for sentid, _ in enumerate(ret_doc['ner']):
        ret_doc['ner'][sentid] = list(sorted(ret_doc['ner'][sentid], key = lambda x: x[0]))


    return ret_doc


def find_tok_idx(doc_char, tokens, is_end = False):
    tok_idx = -1

    for i, token in enumerate(tokens):
        if is_end and token['characterOffsetEnd'] == doc_char:
            return i
        if not is_end and token['characterOffsetBegin'] == doc_char:
            return i 

    return tok_idx



def extract_gold_relations_for_pure(ann_file, text_file, cornelp_file, use_component):

    accept_ner2 = ['Component'] if use_component else ['Element', 'Mineral']

    venue, year, docname, _ = get_docid(text_file)

    doc = json.load(open(cornelp_file, 'r'))

    intrasent_gold_relations = [ (e1, e2, relation) for e1, e2, relation in extract_intrasent_goldrelations_from_ann(ann_file, doc = doc, use_component = use_component) if relation == 'Contains' and e1['label'] == 'Target' and e2['label'] in accept_ner2]
    
    gold_relins = []
    for e1, e2, relation in intrasent_gold_relations:

        sentid = e1['sentid']
        tokens = doc['sentences'][sentid]['tokens']

        sent_toks = [token['word'] for token in tokens]

        ner1 = e1["label"]
        ner2 = e2['label']

        span1 = Span_Instance(venue, year, docname, e1['doc_start_char'], e1['doc_end_char'], e1['text'], ner1)

        span2 = Span_Instance(venue, year, docname, e2['doc_start_char'], e2['doc_end_char'], e2['text'], ner2)

        rel = Rel_Instance(span1, span2, label_str = relation)

        gold_relins.append(rel)

    return gold_relins



def extract_data(ann_files, text_files, corenlp_files, outfile, use_component, max_len = 512, use_sys_ners = False):
    outdir = "/".join(outfile.split("/")[:-1])
    if not exists(outdir):
        os.makedirs(outdir)

    docs = [ extract_data_for_pure(ann_file, text_file, corenlp_file, use_component, max_len = max_len, use_sys_ners = use_sys_ners) for ann_file, text_file, corenlp_file in zip(ann_files, text_files, corenlp_files)]

    print(f"Saving extracted instances to to {outfile}")
    with open(outfile, "w") as f:
        f.write("\n".join([json.dumps(d) for d in docs]))


def extract_gold_data(ann_files, text_files, corenlp_files, outfile, use_component):
    outdir = "/".join(outfile.split("/")[:-1])
    if not exists(outdir):
        os.makedirs(outdir)

    gold_relations = []
    for ann_file, text_file, corenlp_file in zip(ann_files, text_files, corenlp_files):
        gold_relations.extend(extract_gold_relations_for_pure(ann_file, text_file, corenlp_file, use_component))

    print(f"Generated {len(gold_relations)} gold instances for evaluation.")
    print(f"Saving eval set to {outfile}")
    with open(outfile, "wb") as f:
        pickle.dump(gold_relations, f)

def main(args):

    train_annfiles, train_textfiles, train_corenlpfiles = read_inlist(args.train_inlist)
    dev_annfiles, dev_textfiles, dev_corenlpfiles = read_inlist(args.dev_inlist)

    test_annfiles, test_textfiles, test_corenlpfiles = read_inlist(args.test_inlist)

    use_component = True # convert element and mineral to component 


    # ---- make training samples ----
    print("Making training samples ... ")


    assert all([exists(k) for k in train_annfiles + train_textfiles + train_corenlpfiles])

    outfile = "./data/train/docs.json"
    extract_data(train_annfiles, train_textfiles, train_corenlpfiles, outfile, use_component, max_len = args.max_len, use_sys_ners = False)

    # ---- make val samples ----
    print("Making Dev data using gold ners ..")
    assert all([exists(k) for k in dev_annfiles + dev_textfiles + dev_corenlpfiles])

    # use gold ners 
    outfile = "./data/dev/gold_ner/docs.json"
    extract_data(dev_annfiles, dev_textfiles, dev_corenlpfiles, outfile, use_component, max_len = args.max_len, use_sys_ners = False)

    # making evaluation set
    outfile = "./data/dev/gold_relins.pkl"
    extract_gold_data(dev_annfiles, dev_textfiles, dev_corenlpfiles, outfile, use_component)
    
    # -------- make test samples ---------
    print("Making Test data using gold ners ..")
    assert all([exists(k) for k in test_annfiles + test_textfiles + test_corenlpfiles])

    outfile = "./data/test/gold_ner/docs.json"
    extract_data(test_annfiles, test_textfiles, test_corenlpfiles, outfile, use_component, max_len = args.max_len,  use_sys_ners = False)

    outfile = "./data/test/gold_relins.pkl"
    extract_gold_data(test_annfiles, test_textfiles, test_corenlpfiles, outfile, use_component)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument('--train_inlist', required = True, help = "input list of files for TRAIN data. Each line is in the format of '<ann_file>,<text_file>,<corenlp_file>' where <corenlp_file> is the json file that stores the parsing results of the text file using CoreNLP. ")

    parser.add_argument('--dev_inlist', required = True, help = "input list of files for DEV data. It is in the same format as train_inlist ")

    parser.add_argument('--test_inlist', required = True, help = "input list of files for TEST data.  It is in the same format as train_inlist ")

    parser.add_argument('--max_len', type = int, default = 512, help = "maximum of tokens to keep in a sentence after bert tokenization")

    args = parser.parse_args()
    main(args)
 
# Copyright 2021, by the California Institute of Technology. ALL
# RIGHTS RESERVED. United States Government Sponsorship
# acknowledged. Any commercial use must be negotiated with the Office
# of Technology Transfer at the California Institute of Technology.
#
# This software may be subject to U.S. export control laws and
# regulations.  By accepting this document, the user agrees to comply
# with all applicable U.S. export laws and regulations.  User has the
# responsibility to obtain export licenses, or other export authority
# as may be required before exporting such information to foreign
# countries or providing access to foreign persons.

