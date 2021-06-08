import sys, tabulate

from sklearn.metrics import accuracy_score
from sklearn.metrics import precision_recall_fscore_support

from sklearn.metrics import confusion_matrix
import itertools
import numpy as np
import matplotlib.pyplot as plt
from tabulate import tabulate

def test_eval(pred_instances, gold_instances, label_to_eval, tuple_level = False):
    # inputs should be instance-level instances. 

    print(f"there are {len(gold_instances)} gold span instance in relations")
    if tuple_level:
        gold_signatures = set([(ins.doc_id, ins.std_text) for ins in gold_instances if ins.relation_label == label_to_eval])

        pred_signatures = set([(ins.doc_id, ins.std_text) for ins in pred_instances if ins.pred_relation_label == label_to_eval])
    else:

        gold_signatures = set([ins.span_id for ins in gold_instances if ins.relation_label == label_to_eval])
        pred_signatures = set([ins.span_id for ins in pred_instances if ins.pred_relation_label == label_to_eval])
    print(f"There are {len(gold_signatures)} gold span at {'tuple level' if tuple_level else 'instance level'}")
        

    num_correct = len(gold_signatures.intersection(pred_signatures))

    recall = num_correct / len(gold_signatures)
    precision = num_correct / len(pred_signatures) if len(pred_signatures) else 0 

    f1 = 2 * recall * precision / (precision + recall) if precision + recall != 0 else 0 

    return precision, recall, f1

