import sys, tabulate, argparse, pickle
import itertools
import numpy as np
import matplotlib.pyplot as plt
from tabulate import tabulate
from instance import Rel_Instance


def test_eval(pred_instances, gold_instances, label_to_eval):
    # inputs should be instance-level instances. 
    # this is a tuple-based evaluation 

    gold_signatures = set([ins.signature for ins in gold_instances if ins.label == label_to_eval])

    pred_signatures = set([ins.signature for ins in pred_instances if ins.pred_relation_label == label_to_eval])

    num_correct = len(gold_signatures.intersection(pred_signatures))

    recall = num_correct / len(gold_signatures)
    precision = num_correct / len(pred_signatures) if len(pred_signatures) else 0 

    f1 = 2 * recall * precision / (precision + recall) if precision + recall != 0 else 0 

    return precision, recall, f1

def instance_level_eval(pred_instances, gold_instances, label_to_eval):

    gold_signatures = set([ins.re_id for ins in gold_instances if ins.label == label_to_eval])

    pred_signatures = set([ins.re_id for ins in pred_instances if ins.pred_relation_label == label_to_eval])

    num_correct = len(gold_signatures.intersection(pred_signatures))

    recall = num_correct / len(gold_signatures)
    precision = num_correct / len(pred_signatures) if len(pred_signatures) else 0 

    f1 = 2 * recall * precision / (precision + recall) if precision + recall != 0 else 0 

    return precision, recall, f1

def main(args):

    pred_instances = pickle.load(open(args.pred_relins, "rb"))
    
    gold_instances = pickle.load(open(args.gold_relins, "rb"))
    
    precision, recall, f1 = test_eval(pred_instances, gold_instances, 'Contains')
    
    print("Tuple Level")
    print(f"Precision: {precision * 100:.2f}, Recall: {recall * 100:.2f}, F1: {f1 * 100:.2f}")

    precision, recall, f1 = instance_level_eval(pred_instances, gold_instances, 'Contains')

    print("Instance Level")
    print(f"Precision: {precision * 100:.2f}, Recall: {recall * 100:.2f}, F1: {f1 * 100:.2f}")
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--pred_relins", required = True)
    parser.add_argument("--gold_relins", required = True)

    args = parser.parse_args()

    main(args)

