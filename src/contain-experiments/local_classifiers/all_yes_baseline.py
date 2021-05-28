import pickle, sys, argparse 
from os.path import dirname, abspath, join
from copy import deepcopy 
from instance import Rel_Instance, Span_Instance
curpath = dirname(abspath(__file__))
sys.path.append(join(curpath, "relation_model"))
from evaluation import test_eval, instance_level_eval


# python all_yes_baseline.py -test_rels relation_model/rels/test/EM.extracted_gold_relins.pkl -gold_rels relation_model/rels/test/EM.annotated_gold_relins.pkl
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
        
    parser.add_argument("-test_rels",required = True)

    parser.add_argument("-gold_rels",required = True)


    args = parser.parse_args()

    gold_rels = pickle.load(open(args.gold_rels, "rb"))

    rels = pickle.load(open(args.test_rels, "rb"))
    for rel in rels:
        rel.pred_relation_label = "Contains"

    precision, recall, f1 = test_eval(rels, gold_rels, "Contains")
    print(f"TUPLE-LEVEL EVAL of combined prediction: precison: {precision*100:.2f}, recall: {recall*100:.2f}, f1: {f1*100:.2f}")

    precision, recall, f1 = instance_level_eval(rels, gold_rels, "Contains")
    print(f"INSTANCE-LEVEL EVAL of combined prediction: precision: {precision*100:.2f}, recall: {recall*100:.2f}, f1: {f1*100:.2f}")