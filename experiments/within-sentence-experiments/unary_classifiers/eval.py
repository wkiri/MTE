# python3
# predict.py
# Mars Target Encyclopedia
# This script evaluate extracted relations against gold data. 
#
# Yuan Zhuang
# July 30, 2021
# Copyright notice at bottom of file.

import sys, argparse, pickle, os
import itertools
import numpy as np
from os.path import abspath, dirname, join 

curpath = dirname(abspath(__file__))
shared_path = join(dirname(dirname(curpath)), "shared")
sys.path.append(shared_path)
from instance import Span_Instance, Rel_Instance 

def gold_coverage(pred_instances, gold_instances):
    """
     check how many gold instances could be matched in predicted instances
    """
    pred_reids = set([s.re_id for s in pred_instances]) 
    match = 0
    for s in gold_instances:
        if s.re_id in pred_reids:
            match += 1
    print(f"{match}/{len(gold_instances)}({match/len(gold_instances)*100:.2f}%) gold relation instances could be found in predicted instances ")

def analyze_predictions(pred_instances, gold_instances, label_to_eval, outputdir):
    if not os.path.exists(outputdir):
        os.makedirs(outputdir)


    false_positives = open(os.path.join(outputdir, "false_positives.txt"), "w")
    false_negatives = open(os.path.join(outputdir, "false_negatives.txt"), "w")
    true_positives = open(os.path.join(outputdir, "true_positives.txt"), "w")
    true_negatives = open(os.path.join(outputdir, "true_negatives.txt"), "w")


    gold_ids = [ins.re_id for ins in gold_instances if ins.label == label_to_eval]

    print(f"{len(pred_instances)} prediction instances")




    for ins in pred_instances:
        if ins.pred_relation_label == 'Contains' and ins.re_id not in gold_ids:

            # k = f"{ins.span1.docname} {ins.span1.venue} {ins.span1.year} {ins.span1.sentid}" 
            # if len(sentid2target[k]) > 1:
            #     false_positives.write(str(ins) + "\n\n")


            false_positives.write(str(ins) + "\n\n")
        if ins.pred_relation_label != 'Contains' and ins.re_id in gold_ids:
            false_negatives.write(str(ins) + "\n\n")
        if ins.pred_relation_label == 'Contains' and ins.re_id in gold_ids:
            true_positives.write(str(ins) + "\n\n")
        if ins.pred_relation_label != 'Contains' and ins.re_id not in gold_ids:
            true_negatives.write(str(ins) + "\n\n")
    
    false_negatives.close()
    false_positives.close()
    true_positives.close()
    true_negatives.close()





def relation_tuple_eval(pred_instances, gold_instances, label_to_eval, use_all_yes = False):
    # inputs should be instance-level instances. 
    # this is a tuple-based evaluation 

    gold_coverage(pred_instances, gold_instances)

    gold_signatures = set([ins.signature for ins in gold_instances if ins.label == label_to_eval])

    pred_signatures = set([ins.signature for ins in pred_instances if ins.pred_relation_label == label_to_eval])

    if use_all_yes:
        pred_signatures = set([ins.signature for ins in pred_instances])

    num_correct = len(gold_signatures.intersection(pred_signatures))

    recall = num_correct / len(gold_signatures)
    precision = num_correct / len(pred_signatures) if len(pred_signatures) else 0 

    f1 = 2 * recall * precision / (precision + recall) if precision + recall != 0 else 0 

    intersection = len(set([ins.signature for ins in pred_instances]).intersection(gold_signatures))
    coverage_of_gold = intersection/len(gold_signatures)


    print(f"{len(gold_instances)} gold instances ({len(gold_signatures)} gold tuples) in eval set\n There are {len(pred_instances)} predicted instances, with {len([p for p in pred_instances if p.pred_relation_label =='Contains'])} Contains instance ({len(pred_signatures)} Contains tuples).\n {coverage_of_gold*100:.2f}% of gold tuples are matched in the predicted instances.\n {num_correct} of these predicted Contains tuples are correct ")



    return precision, recall, f1

def relation_instance_eval(pred_instances, gold_instances, label_to_eval, analyze = False, analyze_dir = None, use_all_yes = False ):

    gold_signatures = set([ins.re_id for ins in gold_instances if ins.label == label_to_eval])

    pred_signatures = set([ins.re_id for ins in pred_instances if ins.pred_relation_label == label_to_eval])

    if use_all_yes:
        pred_signatures = set([ins.re_id for ins in pred_instances])

    num_correct = len(gold_signatures.intersection(pred_signatures))

    recall = num_correct / len(gold_signatures)
    precision = num_correct / len(pred_signatures) if len(pred_signatures) else 0 

    f1 = 2 * recall * precision / (precision + recall) if precision + recall != 0 else 0 

    if analyze:
        assert analyze_dir is not None 
        print(f"saving analysis to {analyze_dir}")
        analyze_predictions(pred_instances, gold_instances, label_to_eval, analyze_dir)

    return precision, recall, f1

def unary_eval(pred_instances, gold_instances, label_to_eval, tuple_level = False):
    """ this function calculates the performance of Containee/Container over the corresponding test set (e.g. to eval Containee, the test set would be a set of Components with label assigned by Containee model)
    """
    
    print(f"there are {len(gold_instances)} gold span instance with Contains relation")
    
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



def main(args):

    pred_instances = pickle.load(open(args.pred_relins, "rb"))
    
    gold_instances = pickle.load(open(args.gold_relins, "rb"))
    
    precision, recall, f1 = relation_tuple_eval(pred_instances, gold_instances, 'Contains')
    
    print("Tuple Level")
    print(f"Precision: {precision * 100:.2f}, Recall: {recall * 100:.2f}, F1: {f1 * 100:.2f}")

    precision, recall, f1 = relation_instance_eval(pred_instances, gold_instances, 'Contains', args.analyze, args.analyze_dir)

    print("Instance Level")
    print(f"Precision: {precision * 100:.2f}, Recall: {recall * 100:.2f}, F1: {f1 * 100:.2f}")
    
if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("--pred_relins", required = True)
    parser.add_argument("--gold_relins", required = True)

    parser.add_argument("--analyze", default = 0, type = int, help = 'Whether to save the error cases to a file')

    parser.add_argument("--analyze_dir", default = "./temp/analysis", help = 'Output directory of analysis file')

    args = parser.parse_args()

    main(args)

# Copyright 2021, by the California Institute of Technology. ALL
# RIGHTS RESERVED. United States Government Sponsorship
# acknowledged. Any commercial use must be negotiated with the Office
# of Technology Transfer at the California Institute of Technology.
#
# This software may be subject to U.S. export control laws and
# regulations.  By accepting this document, the user agrees to comply
# with all applicable U.S. export laws and regulations.  User has the
# responsibility to obtain export licenses, or other export authority
# as may be required before exporting such information to foreign
# countries or providing access to foreign persons.
