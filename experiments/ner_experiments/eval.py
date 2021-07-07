import sys, tabulate, argparse, pickle, os, re 
import itertools
import numpy as np
import matplotlib.pyplot as plt
from tabulate import tabulate
from instance import Span_Instance

def safe_div(a, b):
    return a/b if b != 0 else 0 

def evaluate(pred_instances, gold_instances, classes = ['Element', 'Mineral', 'Target']):

    print(len(gold_instances))
    print(len(pred_instances))

    golds = {}
    labels = set()
    for ins in gold_instances:
        label = ins.ner_label
        labels.add(label)
        span_id = ins.span_id
        if label not in golds:
            golds[label] = set()
        golds[label].add(span_id)

    preds = {}
    for ins in pred_instances:
        label = ins.ner_label
        span_id = ins.span_id
        if label not in preds:
            preds[label] = set()
        preds[label].add(span_id)

    tp = {}
    fp = {}
    fn = {}
    for label in classes:

        pred_ids = preds.get(label, set())
        gold_ids = golds.get(label, set())

        tp[label] = len(pred_ids.intersection(gold_ids))
        fn[label] = len([id for id in gold_ids if id not in pred_ids])
        fp[label] = len([id for id in pred_ids if id not in gold_ids])
    table = []
    headers = ['Class', 'Precision', 'Recall', 'F1']

    for label in classes:
        precision = safe_div(tp[label], tp[label] + fp[label])
        recall = safe_div(tp[label], tp[label] + fn[label])
        f1 = safe_div(precision * recall * 2, precision + recall)
        table.append([label, f"{precision*100:.2f}", f"{recall*100:.2f}", f"{f1*100:.2f}"])

    # in total 
    precision = safe_div(sum([tp[label] for label in classes]), sum([tp[label] + fp[label] for label in classes]))
    recall = safe_div(sum([tp[label] for label in classes]), sum([tp[label] + fn[label] for label in classes]))
    f1 = safe_div(precision * recall * 2, precision + recall)

    table.append(['Total', precision, recall, f1])

    eval_str = tabulate(table, headers = headers)
    return eval_str

# def word_level_eval(pred_instances, gold_instances):
#     def breakdown(ins):
#         start_char, end_char = ins.doc_start_char, doc_end_char
#         if "-" in ins.text or "_" in ins.text or 

#     preds = [] # doc start, doc end 
#     for ins in pred_instances:
#         if ins.ner_label == 'Target':
#             preds.extend(breakdown(ins))
#     golds = [] 
#     for ins in gold_instances:
#         if ins.ner_label == 'Target':
#             golds.extend(breakdown(ins))




def main(args):

    pred_instances = pickle.load(open(args.prediction, "rb"))

    
    gold_instances = pickle.load(open(args.gold, "rb"))

    print(evaluate(pred_instances,gold_instances))
    
   
if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--prediction", required = True)
    parser.add_argument("--gold", required = True)
    args = parser.parse_args()

    main(args)
