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
from eval import test_eval, instance_level_eval

def combine_prediction(spans, rels, span_is_target, boost_precision = True, boost_recall = True):

    contained_spanids = {span.span_id: span.pred_score for span in spans if span.pred_relation_label == "Contains"}

    new_rels = [deepcopy(rel) for rel in rels] 

    if boost_precision:
        # if span2 is not recognized as contained by anything: change the relation label of the relation instance to O

        for rel in new_rels:
            if span_is_target and  rel.span1.span_id not in contained_spanids:
                rel.pred_relation_label = "O"
            if not span_is_target and  rel.span2.span_id not in contained_spanids:
                rel.pred_relation_label = "O"

    if boost_recall:
        span2rel = {}
        for rel in new_rels:
            span_id = rel.span2.span_id if not span_is_target else rel.span1.span_id
            if span_id not in span2rel:
                span2rel[span_id] = []
            span2rel[span_id].append(rel)

        # if span2 is recognized as contained, and there is no target selected, select the target with the maximum score as related one
        for span_id in span2rel:
            if span_id not in contained_spanids:
                continue
            has_argument = 0
            selected_rel = None
            for rel in span2rel[span_id]:
                if selected_rel is None or rel.pred_score[0] > selected_rel.pred_score[0]:
                    selected_rel = rel
                if rel.pred_relation_label == "Contains":
                    has_argument = 1
                    break
            
            if not has_argument:
                selected_rel.pred_relation_label = "Contains"

    return new_rels


if __name__ == "__main__":


    parser = argparse.ArgumentParser()
    
    parser.add_argument("-spans",required = True)
    parser.add_argument("-rels",required = True)
    parser.add_argument("-gold_rels",required = True)

    parser.add_argument("-boost_precision", type = int, choices = [0,1], required = True)

    parser.add_argument("-boost_recall", type = int, choices = [0,1], required = True)


    args = parser.parse_args()

    spans = pickle.load(open(args.spans, "rb"))
    rels = pickle.load(open(args.rels, "rb"))
    gold_rels = pickle.load(open(args.gold_rels, "rb"))

    span_is_target = "T" in args.spans.split("/")[-1]


    new_rels = combine_prediction(spans, rels, span_is_target, boost_precision = args.boost_precision, boost_recall = args.boost_recall)

    precision, recall, f1 = test_eval(new_rels, gold_rels, "Contains")
    print(f"TUPLE-LEVEL EVAL of combined prediction: precison: {precision*100:.2f}, recall: {recall*100:.2f}, f1: {f1*100:.2f}")

    precision, recall, f1 = instance_level_eval(new_rels, gold_rels, "Contains")
    print(f"INSTANCE-LEVEL EVAL of combined prediction: precision: {precision*100:.2f}, recall: {recall*100:.2f}, f1: {f1*100:.2f}")