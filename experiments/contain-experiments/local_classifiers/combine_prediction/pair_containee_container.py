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

def combine_prediction(targets, components):
    # a pair of target, components from the same sentence if they are predicted with 'Contains' by container and containee resepctively
    sent2entities = {}
    # map to same sentence 
    for t in targets:
        sentid = f"{t.venue},{t.year},{t.docname},{t.sentid}"
        if sentid not in sent2entities:
            sent2entities[sentid] = {
                "Targets":[],
                "Components":[]
            }
        sent2entities[sentid]['Targets'].append(deepcopy(t))
    for c in components:
        sentid = f"{c.venue},{c.year},{c.docname},{c.sentid}"
        if sentid not in sent2entities:
            sent2entities[sentid] = {
                "Targets":[],
                "Components":[]
            }
        sent2entities[sentid]['Components'].append(deepcopy(c))

    new_rels = []
    for sentid in sent2entities:
        components, targets = sent2entities[sentid]['Components'], sent2entities[sentid]['Targets']
        for t in targets:
            for c in components:
                rel = Rel_Instance(t, c)
                if t.pred_relation_label == 'Contains' and c.pred_relation_label == 'Contains':
                    rel.pred_relation_label = 'Contains'
                else:
                    rel.pred_relation_label = 'O'
                new_rels.append(rel)




    return new_rels



if __name__ == "__main__":


    parser = argparse.ArgumentParser()
    
    parser.add_argument("-targets",required = True)
    parser.add_argument("-components",required = True)
    parser.add_argument("-gold_rels",required = True)

    args = parser.parse_args()

    targets = pickle.load(open(args.targets, "rb"))
    components = pickle.load(open(args.components, "rb"))
    gold_rels = pickle.load(open(args.gold_rels, "rb"))

    new_rels = combine_prediction(targets, components)

    precision, recall, f1 = test_eval(new_rels, gold_rels, "Contains")
    print(f"TUPLE-LEVEL EVAL of combined prediction: precison: {precision*100:.2f}, recall: {recall*100:.2f}, f1: {f1*100:.2f}")

    precision, recall, f1 = instance_level_eval(new_rels, gold_rels, "Contains")
    print(f"INSTANCE-LEVEL EVAL of combined prediction: precision: {precision*100:.2f}, recall: {recall*100:.2f}, f1: {f1*100:.2f}")