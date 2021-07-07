# author: Yuan Zhuang 
# This code maps pure prediction back to span_instance and rel_instance such that evaluation is eaiser
import re, pickle, sys, argparse, random, json, os
from copy import deepcopy 
from sys import stdout 
from os.path import abspath, dirname, join, exists
from os import makedirs, listdir
from transformers import *

curpath = dirname(abspath(__file__))
upperpath = dirname(curpath)
sys.path.append(upperpath)
from instance import Span_Instance, Rel_Instance

from extraction_utils import get_docid, extract_gold_entities_from_ann,extract_intrasent_entitypairs_from_text_file, extract_intrasent_goldrelations_from_ann, extract_entities_from_text, get_offset2sentid, get_sentid_from_offset

from scipy.special import softmax

def find_doc_offset(tokens, tok_sidx, tok_eidx):
    # given a token of star idx and end idx, find its token offset in doc 
    start_char = -1
    end_char = -1 

    for i, tok in enumerate(tokens):
        if i == tok_sidx:
            assert start_char == -1
            start_char = tok['characterOffsetBegin']
        if i == tok_eidx:
            assert end_char == -1
            end_char = tok['characterOffsetEnd']
    assert start_char != -1 and end_char != -1
    return start_char, end_char

def main(args):
    use_component = args.use_component
    outfile = args.pred_file.split(".json")[0] + ".pkl"
    corenlp_dir = "../../../parse/"
    ann_dir = "../../../corpus-LPSC"
    accept_ner2 = ['Element', 'Mineral'] if not use_component else ['Component']
    
    ners = [] # store prediction instances
    
    # load predictions 
    predicted_docs = []
    for line in open(args.pred_file, "r").read().strip().split("\n"):
        predicted_docs.append(json.loads(line))

    for docidx, predicted_doc in enumerate(predicted_docs):

        venue, year, docname = predicted_doc['doc_key'].split(',')

        if "lpsc" in venue:
            doc = json.load(open(join(corenlp_dir, venue, docname + ".txt.json"), "r"))
            ann_file = join(ann_dir,venue, docname + ".ann")
            text_file = join(ann_dir,venue, docname + ".txt")
        else:
            doc = json.load(open(join(corenlp_dir, venue, f"{year}_{docname}.txt.json"), "r"))
            ann_file = join(ann_dir,venue, f"{year}_{docname}.ann")
            text_file = join(ann_dir,venue, f"{year}_{docname}.txt")

        # get offset to gold ner label 

        gold_entities = [e for e in extract_gold_entities_from_ann(ann_file, use_component) if e['label'] in ['Target'] + accept_ner2]

        offset2ner = {}
        for e in gold_entities:
            ner = e['label']
            if use_component and ner != 'Target':
                ner = 'Component'

            offset2ner[(e['doc_start_char'], e['doc_end_char'])]= e['label'] if e['label'] == 'Target' else ner

        for sentid, sent_ners in enumerate(predicted_doc['predicted_ner']):
            
            cumu_toks = sum([len(doc['sentences'][s]['tokens']) for s in range(sentid)])
            sent_toks = [w['word'] for w in doc['sentences'][sentid]['tokens']]

            for tok_sidx1, tok_eidx1, ner_label in sent_ners: # eidx is inclusive
                tok_sidx1, tok_eidx1 = tok_sidx1 -cumu_toks, tok_eidx1-cumu_toks

                tokens = doc['sentences'][sentid]['tokens']

                tok1_doc_start_char, tok1_doc_end_char = find_doc_offset(tokens, tok_sidx1 , tok_eidx1)
                
                
                text1 = " ".join([t['word'] for t in tokens[tok_sidx1: tok_eidx1 + 1]])

                span1 = Span_Instance(venue, year, docname, tok1_doc_start_char, tok1_doc_end_char, text1, "", sent_toks = sent_toks )
                span1.pred_ner_label = ner_label
                ners.append(span1)
    # sanity check all ner labels are valid 
    print(set([span.pred_ner_label for span in ners]))
    assert all([span.pred_ner_label in ['Target'] + accept_ner2 for span in ners])

    print(f"saving converted prediction file to {outfile}")
    with open(outfile, "wb") as f:
        pickle.dump(ners, f)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--use_component", type = int, choices = [0,1], required = True)
    parser.add_argument("--pred_file", required = True)

    args = parser.parse_args()
    main(args)
        