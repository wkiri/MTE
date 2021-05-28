import sys, tabulate
import itertools
import numpy as np
import matplotlib.pyplot as plt
from tabulate import tabulate


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
