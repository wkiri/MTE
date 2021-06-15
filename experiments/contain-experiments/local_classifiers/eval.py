import sys, tabulate, argparse, pickle, os
import itertools
import numpy as np
import matplotlib.pyplot as plt
from tabulate import tabulate
from instance import Rel_Instance

def found_gold(pred_instances, gold_instances):
    # check how many gold instances could be matched
    pred_reids = set([s.re_id for s in pred_instances]) 
    match = 0
    for s in gold_instances:
        if s.re_id in pred_reids:
            match += 1
    print(f"{match}/{len(gold_instances)}({match/len(gold_instances)*100:.2f}%) gold relation instances could be found in predicted instances ")

def analyze_predictions(pred_instances, gold_instances, label_to_eval, outputdir):
    if not os.path.exists(outputdir):
        os.makedirs(outputdir)

    # === false cases 
    gold_signatures = set([ins.signature for ins in gold_instances if ins.label == label_to_eval])
    gold_ids = set([ins.re_id for ins in gold_instances if ins.label == label_to_eval])
    print(f"Saving analysis to {outputdir}, false_positive.txt and false_negatives.txt")
    false_positives = open(os.path.join(outputdir, "false_positives.txt"), "w")
    # false_negatives = open(os.path.join(outputdir, "false_negatives.txt"), "w")
    # true_positives = open(os.path.join(outputdir, "true_positives.txt"), "w")
    true_negatives = open(os.path.join(outputdir, "true_negatives.txt"), "w")

    count_fp = 0 
    # count_fn = 0 
    # count_tp = 0 
    count_tn = 0 
    for ins in pred_instances:
        pred_score = ins.pred_score
        pred_label = ins.pred_relation_label
        gold_label = 'Contains' if ins.signature in gold_signatures else 'O'

        if ins.pred_relation_label == label_to_eval and ins.signature not in gold_signatures:
            false_positives.write(f"{count_fp}:\n{ins}\nSCORE = {pred_score}\nPRED label: {pred_label}, GOLD label: {gold_label}\n\n")
            count_fp += 1

        # # if ins.pred_relation_label == 'O' and ins.re_id in gold_signatures:
        # #     false_negatives.write(f"{count_fn}:\n{ins}\nSCORE = {pred_score}\nPRED label: {pred_label}, GOLD label: {gold_label}\n\n")
        #     count_fn += 1
        
        # if ins.pred_relation_label == 'Contains' and ins.signature in gold_signatures:
        #     true_positives.write(f"{count_tp}:\n{ins}\nSCORE = {pred_score}\nPRED label: {pred_label}, GOLD label: {gold_label}\n\n")
        #     count_tp += 1
        
        if ins.pred_relation_label == 'O' and ins.signature not in gold_signatures:
            true_negatives.write(f"{count_tn}:\n{ins}\nSCORE = {pred_score}\nPRED label: {pred_label}, GOLD label: {gold_label}\n\n")
            count_tn += 1


    false_positives.close()
    # false_negatives.close()
    # true_positives.close()
    true_negatives.close()




def test_eval(pred_instances, gold_instances, label_to_eval, use_all_yes = False):
    # inputs should be instance-level instances. 
    # this is a tuple-based evaluation 

    found_gold(pred_instances, gold_instances)

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

def instance_level_eval(pred_instances, gold_instances, label_to_eval, analyze = False, analyze_dir = None, use_all_yes = False ):

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
        analyze_predictions(pred_instances, gold_instances, label_to_eval, analyze_dir)

    return precision, recall, f1

def main(args):

    pred_instances = pickle.load(open(args.pred_relins, "rb"))
    
    gold_instances = pickle.load(open(args.gold_relins, "rb"))
    
    precision, recall, f1 = test_eval(pred_instances, gold_instances, 'Contains', args.use_all_yes)
    
    print("Tuple Level")
    print(f"Precision: {precision * 100:.2f}, Recall: {recall * 100:.2f}, F1: {f1 * 100:.2f}")

    precision, recall, f1 = instance_level_eval(pred_instances, gold_instances, 'Contains', args.analyze, args.analyze_dir, args.use_all_yes)

    print("Instance Level")
    print(f"Precision: {precision * 100:.2f}, Recall: {recall * 100:.2f}, F1: {f1 * 100:.2f}")
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--pred_relins", required = True)
    parser.add_argument("--gold_relins", required = True)
    parser.add_argument("--analyze", default = 0, type = int)
    parser.add_argument("--use_all_yes", default = 0, type = int)
    parser.add_argument("--analyze_dir", default = "./temp/analysis")
    args = parser.parse_args()

    main(args)
