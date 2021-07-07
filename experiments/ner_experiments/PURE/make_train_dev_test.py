# author: Yuan Zhuang 
# This code make train, dev and test set 
import re, pickle, sys, argparse, random, json, os
from copy import deepcopy 
from sys import stdout 
from os.path import abspath, dirname, join, exists
from os import makedirs, listdir
from transformers import *

# curpath = dirname(abspath(__file__))
curpath = abspath(".")
upperpath = dirname(curpath)
sys.path.append(upperpath)
from instance import Span_Instance, Rel_Instance
from extraction_utils import get_docid, extract_gold_entities_from_ann,extract_entities_from_text, get_offset2sentid, get_sentid_from_offset


parentpath = dirname(upperpath)



def extract_data_for_pure(ann_file, text_file, corenlp_file,  use_component, max_len = 512):

    accept_ner2 = ['Component'] if use_component else ['Element', 'Mineral']

    venue, year, docname, _ = get_docid(text_file)

    doc = json.load(open(corenlp_file, 'r'))

    ret_doc = {"ner": [], 
    "sentences": [ [token['word'] for token in sent['tokens']] for sent in doc["sentences"]], 
    "doc_key": f"{venue},{year},{docname}",
    } 
    ret_doc["ner"] = [[] for _ in ret_doc['sentences']]

    # group entities by sentence id.
    for e1 in extract_entities_from_text(text_file, ann_file, doc = doc, use_component = use_component, be_quiet = True):
        sentid = e1['sentid']

        sent_toks = ret_doc['sentences'][sentid]
        cum_toks = sum([len(ret_doc["sentences"][i]) for i in range(sentid)])


        ner1 = e1["label"]
        if ner1 not in ['Target'] + accept_ner2:
            continue
        
        span1_doc_start_char = e1["doc_start_char"]
        span1_doc_end_char = e1["doc_end_char"]

        span1 = [e1["sent_start_idx"] + cum_toks, e1["sent_end_idx"] - 1 + cum_toks, ner1]

        # do not include duplicates
        if tuple(span1) not in set([tuple(s) for s in ret_doc['ner'][sentid]]):
            ret_doc["ner"][sentid].append(span1)

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



def extract_gold_entities_for_pure(ann_file, text_file, use_component):

    accept_ner2 = ['Element', 'Mineral'] if not use_component else ['Component']
    venue, year, docname, _ = get_docid(text_file)

    gold_entities = []

    for e1 in  extract_gold_entities_from_ann(ann_file, use_component = use_component):

        ner1 = e1["label"]
        if ner1 not in ['Target'] + accept_ner2:
            continue

        span1 = Span_Instance(venue, year, docname, e1['doc_start_char'], e1['doc_end_char'], e1['text'], ner1)
        gold_entities.append(span1)

    return gold_entities


def extract_data(ann_files, text_files, corenlp_files, outfile, use_component):
    outdir = "/".join(outfile.split("/")[:-1])
    if not exists(outdir):
        os.makedirs(outdir)

    docs = [ extract_data_for_pure(ann_file, text_file, corenlp_file, use_component) for ann_file, text_file, corenlp_file in zip(ann_files, text_files, corenlp_files)]

    print(f"Saving to {outfile}")
    with open(outfile, "w") as f:
        f.write("\n".join([json.dumps(d) for d in docs]))

def extract_gold_data(ann_files, text_files, corenlp_files, outfile, use_component):
    outdir = "/".join(outfile.split("/")[:-1])
    if not exists(outdir):
        os.makedirs(outdir)

    gold_entities = []
    for ann_file, text_file, corenlp_file in zip(ann_files, text_files, corenlp_files):
        gold_entities.extend(extract_gold_entities_for_pure(ann_file, text_file, use_component))

    print(f"generated {len(gold_entities)} gold instances for evaluation.")
    print(f"saving to {outfile}")
    with open(outfile, "wb") as f:
        pickle.dump(gold_entities, f)

def main(args):
    use_component = args.use_component

    proj_path = dirname(dirname(dirname(curpath)))
    datadir_prefix = join(proj_path, "corpus-LPSC")
    corenlpdir_prefix = join(proj_path, 'parse') # no sys ner predictions 

    # ---- make training samples ----
    print(" ----- making training samples ... ")

    ann15_indir = join(datadir_prefix, "lpsc15-C-raymond-sol1159-v3-utf8")
    corenlp15_indir = join(corenlpdir_prefix, "lpsc15-C-raymond-sol1159-v3-utf8")


    train_annfiles = [join(ann15_indir, file) for file in listdir(ann15_indir) if file.endswith(".ann")][:42]
    train_textfiles = [join(ann15_indir, file.split(".ann")[0] + ".txt") for file in train_annfiles]
    train_corenlpfiles = [join(corenlp15_indir, file.split("/")[-1].split(".ann")[0] + ".txt.json") for file in train_annfiles]

    assert all([exists(k) for k in train_annfiles + train_textfiles + train_corenlpfiles])
    print("> Making Training data")
    outfile = "./data/train.json"
    extract_data(train_annfiles, train_textfiles, train_corenlpfiles, outfile, use_component)

    # ---- make val samples ----
  
    dev_annfiles = [join(ann15_indir, file) for file in listdir(ann15_indir) if file.endswith(".ann")][42:]
    dev_textfiles = [join(ann15_indir, file.split(".ann")[0] + ".txt") for file in dev_annfiles]
    dev_corenlpfiles = [join(corenlp15_indir, file.split("/")[-1].split(".ann")[0] + ".txt.json") for file in dev_annfiles]

    assert all([exists(k) for k in dev_annfiles + dev_textfiles + dev_corenlpfiles])

    print("> Making Dev data using gold ners")
    # use gold ners 
    outfile = "./data/dev.json"
    extract_data(dev_annfiles, dev_textfiles, dev_corenlpfiles, outfile, use_component)


    print("> Making Dev evaluation data")
    # making evaluation set
    outfile = "./data/dev_golds.pkl"
    extract_gold_data(dev_annfiles, dev_textfiles, dev_corenlpfiles, outfile, use_component)

    # -------- make test samples ---------


    test_venues = args.test_venues
    
    test_annfiles = []
    test_textfiles = []
    test_corenlpfiles = []
    for venue in test_venues:
        ann_files =[join(datadir_prefix, venue, file) for file in listdir(join(datadir_prefix, venue)) if file.endswith(".ann")]

        text_files = [file.split(".ann")[0] + ".txt" for file in ann_files]

        corenlp_files =[join(corenlpdir_prefix, venue, file.split("/")[-1] + ".json") for file in text_files]

        test_annfiles.extend(ann_files)
        test_textfiles.extend(text_files)
        test_corenlpfiles.extend(corenlp_files)

    assert all([exists(k) for k in test_annfiles + test_textfiles + test_corenlpfiles])

    print("> Making Test data using gold ners")
    outfile = "./data/test.json"
    extract_data(test_annfiles, test_textfiles, test_corenlpfiles, outfile, use_component)

    print("> Making Test evaluation ")
    outfile = "./data/test_golds.pkl"
    extract_gold_data(test_annfiles, test_textfiles, test_corenlpfiles, outfile, use_component)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--test_venues", nargs = "+", required = True)
    parser.add_argument("--use_component", type = int, choices = [0,1], required = True)

    args = parser.parse_args()
    main(args)
 
