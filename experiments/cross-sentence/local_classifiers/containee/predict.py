import os, sys, argparse, torch, pickle, random, json, numpy as np
from transformers import *
from torch.utils.data import DataLoader
from os.path import abspath, dirname, join, exists
from sys import stdout
import numpy as np
from copy import deepcopy
from dataset import MyDataset, collate
from evaluation import test_eval
from model import Model

# label info 
curpath = dirname(abspath(__file__))
upperpath = dirname(curpath)
sys.path.append(upperpath)
from config import label2ind, ind2label,tokenizer_type


tokenizer = BertTokenizerFast.from_pretrained(tokenizer_type)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


from tabulate import tabulate 

def add_marker_tokens(tokenizer, ner_labels):
    new_tokens = []
    for label in ner_labels:
        new_tokens.append('<ner_start=%s>'%label.lower())
        new_tokens.append('<ner_end=%s>'%label.lower())
    tokenizer.add_tokens(new_tokens)

def analayze(pred_instances, val_gold_ins, dev_analysis_outdir):

    print(f"saving analysis to {dev_analysis_outdir}, error and correct.txt'")

    with open(join(dev_analysis_outdir, "error.txt"), "w") as f:
        for ins in sorted(pred_instances, key = lambda x: (x.doc_id, x.sentid)):
            if ins.relation_label != ins.pred_relation_label:
                f.write(f"DOC: {ins.doc_id}\nSENT: {' '.join(ins.sent_toks)}\nTEXT: {ins.text}\nINPUTIDS: {' '.join(tokenizer.convert_ids_to_tokens(ins.input_ids))}\nHEAD:{tokenizer.convert_ids_to_tokens(ins.input_ids)[ins.bert_start_idx]}\nPRED: {ins.pred_relation_label}, LABEL: {ins.relation_label}\nSCORE: {[f'{s*100:.2f}' for s in ins.pred_score]}\n\n")

    with open(join(dev_analysis_outdir, "correct.txt"), "w") as f:
        for ins in sorted(pred_instances, key = lambda x: (x.doc_id, x.sentid)):
            if ins.relation_label == ins.pred_relation_label and ins.pred_relation_label != "O":
                f.write(f"DOC: {ins.doc_id}\nSENT: {' '.join(ins.sent_toks)}\nTEXT: {ins.text}\nPRED: {ins.pred_relation_label}, LABEL: {ins.relation_label}\n\n")

# evaluate a trained model over validation set and save if achieves better performance 
def eval_and_save(model, val_dataloader, val_gold_ins,  best_f1, args, label_to_eval = "Contains", tuple_level = False, save_prediction = False, threshold = 0.5, use_all_yes = 0): 

    print("\n\n---------------eval------------------\n")
    pred_instances = predict(model, val_dataloader, threshold = threshold)

    if use_all_yes:
        for ins in pred_instances:
            ins.pred_relation_label = 'Contains'

    precision, recall, f1 = test_eval(pred_instances, val_gold_ins, label_to_eval, tuple_level = tuple_level)

    score_str = f"precision: {precision*100:.2f}, recall: {recall*100:.2f}, f1: {f1*100:.2f}\n"



    print(f"------------ Evaluation ------------\n\n{score_str}\n")

    if args.analyze_dev:
        analayze(pred_instances, val_gold_ins, args.outdir)

    if save_prediction:
        print(f"saving prediction to {join(args.outdir, f'spans.pred')}")
        with open(join(args.outdir, f"spans.pred"), "wb") as f:
            pickle.dump(pred_instances, f)
   

    return best_f1



def predict(model, dataloader, threshold = 0.5):
    # dataloader needs to return ids, input_ids, and attention_masks
    
    model = model.to(device)
    model.eval()
    
    pred_instances = []
    soft = torch.nn.Softmax(dim = 1)

    # ids is for tracking 
    with torch.no_grad():  
        for i, item in enumerate(dataloader):
            
            stdout.write(f"\rpredicting {i}/{len(dataloader)}")
            stdout.flush()

            logits =model.forward(item)
            scores = soft(logits).cpu().numpy()
            y_preds = np.argmax(scores,1)


            for ins, y_pred, score in zip(item["instances"], y_preds, scores):
                if score[0] > threshold:
                    y_pred = 0
                else:
                    y_pred = 1
                ins.pred_relation_label = ind2label[y_pred]
                ins.pred_score = score
                pred_instances.append(ins)

    return pred_instances

if __name__ == "__main__":


    """ ================= parse =============== """
    parser = argparse.ArgumentParser()
    

    parser.add_argument('-threshold', default = 0.5, type = float)
    parser.add_argument('-use_all_yes', default = 0, type = int, choices = [0,1], help = "whether to run all yes baseline")


    parser.add_argument("-modelfile", required = True)
    parser.add_argument("-test_dir", default = None)
    parser.add_argument("-outdir", default = "./temp/prediction", help = "where to save the model to")
    parser.add_argument("-dropout", type = float, default = 0)
    parser.add_argument("-analyze_dev", default = False)


    args = parser.parse_args()


    ners = ['Component']

    add_marker_tokens(tokenizer, ners)

    print(">>> loading data ")

    test_file = join(args.test_dir, 
        "spanins.pkl")


    with open(test_file, "rb") as f:
        test_ins = pickle.load(f)

  
    with open(join(args.test_dir, "gold_spanins.pkl"), "rb") as f:
            test_gold_ins = pickle.load(f)

#     """ ================ make dataset ================ """
    print(">>> making dataset ... ")
    test_dataset = MyDataset(test_ins)

#     """ ================ make dataloader ============= """
    print(">>> making data loader ...")
    test_dataloader = DataLoader(test_dataset, batch_size = 10, collate_fn = collate)
#     # """ ================ model ================ """

    model = Model(tokenizer,args)
    model.load_state_dict(torch.load(args.modelfile))

    print("Instance Level Evaluation: ")
    eval_and_save(model, test_dataloader, test_gold_ins, None, args, tuple_level = False, save_prediction = False, threshold = args.threshold)
    print("Tuple Level Evaluation:")
    eval_and_save(model, test_dataloader, test_gold_ins, None, args, tuple_level = True, save_prediction = True, threshold = args.threshold)
    if args.use_all_yes:
        print(">>> All yes baseline")
        print("Tuple Level: ")
        eval_and_save(model, test_dataloader, test_gold_ins, None, args, tuple_level = True, save_prediction = False, threshold = args.threshold, use_all_yes = True)
        print("Instance Level:")
        eval_and_save(model, test_dataloader, test_gold_ins, None, args, tuple_level = False, save_prediction = False, threshold = args.threshold, use_all_yes = True)




  