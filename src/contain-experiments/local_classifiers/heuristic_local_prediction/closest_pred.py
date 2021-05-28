import os, sys, argparse, torch, pickle, random, json, numpy as np
from os.path import abspath, dirname, join, exists
from sys import stdout

from copy import deepcopy 

# # test function
curpath = dirname(abspath(__file__))
upperpath = dirname(curpath)
sys.path.append(upperpath)
from instance import Rel_Instance, Span_Instance
from config import label2ind, ind2label

eval_path = join(upperpath, "relation_model")
sys.path.append(eval_path)
from evaluation import test_eval, instance_level_eval

def find_closest_rel(span, docidsentid2rels, span_is_target = False):
    doc_id, sentid = span.doc_id, span.sentid

    closest_rel = None
    rels = docidsentid2rels.get((doc_id, sentid), [])
    min_dist = 0
    for rel in rels:
        if span_is_target and rel.span1.span_id != span.span_id: continue
        if not span_is_target and rel.span2.span_id != span.span_id: continue

        if span_is_target:
            dist = min(abs(rel.span2.sent_start_idx - span.sent_start_idx), abs(rel.span2.sent_end_idx - 1 - span.sent_start_idx), abs(rel.span2.sent_start_idx - span.sent_end_idx), abs(rel.span2.sent_end_idx - 1 - span.sent_end_idx))
        else:
            dist = min(abs(rel.span1.sent_start_idx - span.sent_start_idx), abs(rel.span1.sent_end_idx - 1 - span.sent_start_idx), abs(rel.span1.sent_start_idx - span.sent_end_idx), abs(rel.span1.sent_end_idx - 1 - span.sent_end_idx))
        # if doc_id == "16_1536":
        #     print(rel)
        #     print(dist, min_dist)
        #     print()
        if closest_rel is None:
            min_dist = dist    
            closest_rel = rel
        else:
            if dist < min_dist:
                closest_rel = rel
                min_dist = dist 
    return closest_rel 

def closest_prediction(spans, rels, span_is_target):

    docidsentid2rels = {}
    for rel in rels:
        key = rel.span1.doc_id, rel.span1.sentid
        if key not in docidsentid2rels:
            docidsentid2rels[key] = []
        docidsentid2rels[key].append(rel)

    print(f"{len([1 for span in spans if span.pred_relation_label == 'Contains'])} positive spans")


    positive_reids = set()
    for span in spans:
        if span.pred_relation_label == "Contains":
            rel = find_closest_rel(span, docidsentid2rels, span_is_target)
            rel.pred_relation_label = "Contains"
            positive_reids.add(rel.re_id)
    for rel in rels:
        if rel.re_id not in positive_reids:
            rel.pred_relation_label = "O"

    return rels, positive_reids



def sanitycheck(spans, rels, span_is_target):

    spanids = set([span.span_id for span in spans])
    if span_is_target:
        rel_spanids = set([rel.span1.span_id for rel in rels ])
    else:
        rel_spanids = set([rel.span2.span_id for rel in rels ])
    print(f"{len(rel_spanids - spanids)} spanids in rels that are not found in spans:", rel_spanids - spanids)
    print()
    print(f"{len(spanids - rel_spanids)} spanids in spans that are not found in rels:", spanids - rel_spanids)




if __name__ == "__main__":


    parser = argparse.ArgumentParser()
    
    parser.add_argument("-spans",required = True)
    parser.add_argument("-rels",required = True)
    parser.add_argument("-gold_rels",required = True)



    args = parser.parse_args()

    spans = pickle.load(open(args.spans, "rb"))
    rels = pickle.load(open(args.rels, "rb"))
    gold_rels = pickle.load(open(args.gold_rels, "rb"))

    span_is_target = "T" in args.spans.split("/")[-1]
    sanitycheck(spans, rels, span_is_target)

    new_rels, positive_pairs = closest_prediction(spans, rels, span_is_target)

    precision, recall, f1 = test_eval(new_rels, gold_rels, "Contains")
    print(f"TUPLE-LEVEL EVAL of combined prediction: precison: {precision*100:.2f}, recall: {recall*100:.2f}, f1: {f1*100:.2f}")

    precision, recall, f1 = instance_level_eval(new_rels, gold_rels, "Contains")
    print(f"INSTANCE-LEVEL EVAL of combined prediction: precision: {precision*100:.2f}, recall: {recall*100:.2f}, f1: {f1*100:.2f}")







 
