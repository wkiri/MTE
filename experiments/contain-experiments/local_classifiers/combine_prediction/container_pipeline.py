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

def combine_prediction(targets, rels, boost_precision = True, boost_recall = True, select_topk = True, topk = 1, joint_score = False):
    assert select_topk + joint_score == 1


    contains_spanids = {span.span_id: span.pred_score for span in targets if span.pred_relation_label == "Contains"}

    new_rels = [deepcopy(rel) for rel in rels] 

    if boost_precision:
        # if targets is not recognized as contains anything: change the relation label of the relation instance to O

        for rel in new_rels:
            if rel.span1.span_id not in contains_spanids and rel.pred_relation_label == 'Contains':
                    rel.pred_relation_label = "O"
        

    if boost_recall:
        target2rel = {}
        for rel in new_rels:
            span_id = rel.span1.span_id
            if span_id not in target2rel:
                target2rel[span_id] = []
            target2rel[span_id].append(rel)

        # if target is recognized as contains, and there is no component selected, select k components with the maximum score as related one
        for span_id in target2rel:
            contains_by_container = span_id in contains_spanids
            contains_by_pure = any([rel.pred_relation_label == 'Contains' for rel in target2rel[span_id]]) # whether pure has already assigned this target to any component
            if contains_by_container and not contains_by_pure:
                this_rels = sorted(target2rel[span_id], key = lambda x: x.pred_score[0], reverse = True)
                for i, rel in enumerate(this_rels):
                    if select_topk:
                        if i<topk:
                            rel.pred_relation_label = 'Contains'
                    if joint_score:
                        raise NameError("Unsupported joint prediction for now")


    return new_rels



if __name__ == "__main__":


    parser = argparse.ArgumentParser()
    
    parser.add_argument("-targets",required = True)
    parser.add_argument("-rels",required = True)
    parser.add_argument("-gold_rels",required = True)

    parser.add_argument("-boost_precision", type = int, choices = [0,1], required = True)

    parser.add_argument("-boost_recall", type = int, choices = [0,1], required = True)


    args = parser.parse_args()

    targets = pickle.load(open(args.targets, "rb"))
    rels = pickle.load(open(args.rels, "rb"))

    gold_rels = pickle.load(open(args.gold_rels, "rb"))

    new_rels = combine_prediction(targets, rels,  boost_precision = args.boost_precision, boost_recall = args.boost_recall)

    precision, recall, f1 = test_eval(new_rels, gold_rels, "Contains")
    print(f"TUPLE-LEVEL EVAL of combined prediction: precison: {precision*100:.2f}, recall: {recall*100:.2f}, f1: {f1*100:.2f}")

    precision, recall, f1 = instance_level_eval(new_rels, gold_rels, "Contains")
    print(f"INSTANCE-LEVEL EVAL of combined prediction: precision: {precision*100:.2f}, recall: {recall*100:.2f}, f1: {f1*100:.2f}")