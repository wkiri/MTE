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

parentpath = dirname(upperpath)
sys.path.insert(0, parentpath)
from extraction_utils import get_docid, extract_gold_entities_from_ann,extract_intrasent_entitypairs_from_text_file, extract_intrasent_goldrelations_from_ann, extract_entities_from_text, get_offset2sentid, get_sentid_from_offset



def extract_data_for_pure(ann_file, text_file, cornelp_file,  max_len = 512):

    venue, year, docname, _ = get_docid(text_file)

    doc = json.load(open(cornelp_file, 'r'))

    intrasent_gold_relations = [ (e1, e2, relation) for e1, e2, relation in extract_intrasent_goldrelations_from_ann(ann_file, doc = doc) if relation == 'Contains' and e1['label'] == 'Target' and e2['label'] in ['Element', 'Mineral']]
    gold_relation_ids = set([f"{e1['venue']},{e1['year']},{e1['docname']},{e1['doc_start_char']},{e1['doc_end_char']},{e2['doc_start_char']},{e2['doc_end_char']}" for e1, e2, relation in intrasent_gold_relations])


    ret_doc = {"ner": [], 
    "sentences": [ [token['word'] for token in sent['tokens']] for sent in doc["sentences"]], 
    "doc_key": f"{venue},{year},{docname}",
    "relations": [],
    } 
    ret_doc["ner"] = [[] for _ in ret_doc['sentences']]
    ret_doc["relations"] = [[] for _ in ret_doc['sentences']]

    entities = [e for e in extract_entities_from_text(text_file, ann_file, doc = doc) if e['label'] in ['Target', 'Element', 'Mineral']]

    # group entities by sentence id.
    sentence_entities = [[] for _ in ret_doc['sentences']]
    for e in entities:
        sentid = e['sentid']
        sentence_entities[sentid].append(e)


    # entities is a list of list, each list is a sentence. here we take only entity pairs from the same sentence
    for sentid, entities in enumerate(sentence_entities):
        ners = []
        relations = []
        sent_toks = ret_doc['sentences'][sentid]

        for i in range(len(entities)):
            e1 = entities[i]
            ner1 = e1["label"]

            if ner1 not in ['Target', 'Element', 'Mineral']:
                continue

            if ner1 in ['Element', 'Mineral']:
                ner1 = 'Component'
            
            span1_doc_start_char = e1["doc_start_char"]
            span1_doc_end_char = e1["doc_end_char"]

            cum_toks = sum([len(ret_doc["sentences"][i]) for i in range(sentid)])
            span1 = [e1["sent_start_idx"] + cum_toks, e1["sent_end_idx"] - 1 + cum_toks, ner1]

   
            ners.append(span1)


            for j in range(len(entities)):
                if j == i: continue
                e2 = entities[j]
                ner2 = e2['label']

                if ner1 != 'Target' or ner2 not in ['Element', 'Mineral']:
                    continue

                # changed label to component 
                ner2 = 'Component'

                span2_doc_start_char = e2["doc_start_char"]
                span2_doc_end_char = e2["doc_end_char"]

                span2 = [e2["sent_start_idx"] + cum_toks,e2["sent_end_idx"] - 1 + cum_toks, ner2]

                if f"{e1['venue']},{e1['year']},{e1['docname']},{e1['doc_start_char']},{e1['doc_end_char']},{e2['doc_start_char']},{e2['doc_end_char']}" in gold_relation_ids:

                    relations.append([span1[0], span1[1], span2[0], span2[1], 'Contains'])

        ret_doc["ner"][sentid] = list(sorted(ners, key = lambda x: x[0]))
        ret_doc["relations"][sentid] = relations

    return ret_doc


def find_tok_idx(doc_char, tokens, is_end = False):
    tok_idx = -1

    for i, token in enumerate(tokens):
        if is_end and token['characterOffsetEnd'] == doc_char:
            return i
        if not is_end and token['characterOffsetBegin'] == doc_char:
            return i 

    return tok_idx



def extract_gold_relations_for_pure(ann_file, text_file, cornelp_file):

    venue, year, docname, _ = get_docid(text_file)

    doc = json.load(open(cornelp_file, 'r'))

    intrasent_gold_relations = [ (e1, e2, relation) for e1, e2, relation in extract_intrasent_goldrelations_from_ann(ann_file, doc = doc) if relation == 'Contains' and e1['label'] == 'Target' and e2['label'] in ['Element', 'Mineral']]
    
    gold_relins = []
    for e1, e2, relation in intrasent_gold_relations:

        sentid = e1['sentid']
        tokens = doc['sentences'][sentid]['tokens']

        sent_toks = [token['word'] for token in tokens]

        ner1 = e1["label"]
        ner2 = e2['label']

        # change label to component 
        ner2 = 'Component'

        span1 = Span_Instance(venue, year, docname, e1['doc_start_char'], e1['doc_end_char'], e1['text'], ner1)

        span2 = Span_Instance(venue, year, docname, e2['doc_start_char'], e2['doc_end_char'], e2['text'], ner2)

        rel = Rel_Instance(span1, span2, label_str = relation)

        gold_relins.append(rel)

    return gold_relins



def extract_data(ann_files, text_files, corenlp_files, outfile):
    outdir = "/".join(outfile.split("/")[:-1])
    if not exists(outdir):
        os.makedirs(outdir)

    docs = [ extract_data_for_pure(ann_file, text_file, corenlp_file) for ann_file, text_file, corenlp_file in zip(ann_files, text_files, corenlp_files)]

    print(f"saving to {outfile}")
    with open(outfile, "w") as f:
        f.write("\n".join([json.dumps(d) for d in docs]))


def extract_gold_data(ann_files, text_files, corenlp_files, outfile):
    outdir = "/".join(outfile.split("/")[:-1])
    if not exists(outdir):
        os.makedirs(outdir)

    gold_relations = []
    for ann_file, text_file, corenlp_file in zip(ann_files, text_files, corenlp_files):
        gold_relations.extend(extract_gold_relations_for_pure(ann_file, text_file, corenlp_file))

    print(f"generated {len(gold_relations)} gold instances for evaluation.")
    print(f"saving to {outfile}")
    with open(outfile, "wb") as f:
        pickle.dump(gold_relations, f)

def main(args):

    proj_path = dirname(dirname(dirname(dirname(curpath))))
    datadir_prefix = join(proj_path, "corpus-LPSC")
    corenlpdir_prefix = join(proj_path, 'parse')
    print(corenlpdir_prefix)

    # ---- make training samples ----
    print(" ----- making training samples ... ")

    ann15_indir = join(datadir_prefix, "lpsc15-C-raymond-sol1159-v3-utf8")
    corenlp15_indir = join(corenlpdir_prefix, "lpsc15-C-raymond-sol1159-v3-utf8")

    train_annfiles = [join(ann15_indir, file) for file in listdir(ann15_indir) if file.endswith(".ann")][:42]
    train_textfiles = [join(ann15_indir, file.split(".ann")[0] + ".txt") for file in train_annfiles]
    train_corenlpfiles = [join(corenlp15_indir, file.split("/")[-1].split(".ann")[0] + ".txt.json") for file in train_annfiles]

    assert all([exists(k) for k in train_annfiles + train_textfiles + train_corenlpfiles])
    
    outfile = "train/docs.json"
    extract_data(train_annfiles, train_textfiles, train_corenlpfiles, outfile)

    # ---- make val samples ----
    print(" ----- making dev samples ... ")
  
    dev_annfiles = [join(ann15_indir, file) for file in listdir(ann15_indir) if file.endswith(".ann")][42:]
    dev_textfiles = [join(ann15_indir, file.split(".ann")[0] + ".txt") for file in dev_annfiles]
    dev_corenlpfiles = [join(corenlp15_indir, file.split("/")[-1].split(".ann")[0] + ".txt.json") for file in dev_annfiles]
    assert all([exists(k) for k in dev_annfiles + dev_textfiles + dev_corenlpfiles])

    outfile = "dev/docs.json"
    extract_data(dev_annfiles, dev_textfiles, dev_corenlpfiles, outfile)

    # -------- make test samples ---------
    print(" ----- making test samples ... ")

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

    outfile = "test/docs.json"
    extract_data(test_annfiles, test_textfiles, test_corenlpfiles, outfile)
    outfile = "test/gold_relins.pkl"
    extract_gold_data(test_annfiles, test_textfiles, test_corenlpfiles, outfile)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--test_venues", nargs = "+", required = True)
    args = parser.parse_args()
    main(args)
 



