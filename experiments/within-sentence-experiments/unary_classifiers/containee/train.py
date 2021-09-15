# python3
# predict.py
# Mars Target Encyclopedia
# This script trains a Containee model. 
#
# Yuan Zhuang
# July 30, 2021
# Copyright notice at bottom of file.

import os, sys, argparse, torch, pickle, random, json, numpy as np
from os.path import abspath, dirname, join, exists
from transformers import *
from torch.utils.data import DataLoader
from os.path import abspath, dirname, join, exists
from sys import stdout
from copy import deepcopy

from model import Model
from dataset import MyDataset, collate
# # test function
from predict import predict

curpath = dirname(abspath(__file__))
upperpath = dirname(curpath)
sys.path.append(upperpath)

from config import label2ind, ind2label,  tokenizer_type

from eval import unary_eval 

exppath = dirname(dirname(dirname(curpath)))
shared_path = join(dirname(dirname(upperpath)), 'shared')
sys.path.insert(0, shared_path)
from other_utils import add_marker_tokens


tokenizer = BertTokenizerFast.from_pretrained(tokenizer_type)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def seed_everything(seed):
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True

def analayze(pred_instances, val_gold_ins, dev_analysis_outdir):

    print(f"Saving analysis to {dev_analysis_outdir}, error and correct.txt'")

    with open(join(dev_analysis_outdir, "error.txt"), "w") as f:
        for ins in sorted(pred_instances, key = lambda x: (x.doc_id, x.sentid)):
            if ins.relation_label != ins.pred_relation_label:
                f.write(f"DOC: {ins.doc_id}\nSENT: {' '.join(ins.sent_toks)}\nTEXT: {ins.text}\nINPUTIDS: {' '.join(tokenizer.convert_ids_to_tokens(ins.input_ids))}\nHEAD:{tokenizer.convert_ids_to_tokens(ins.input_ids)[ins.bert_start_idx]}\nPRED: {ins.pred_relation_label}, LABEL: {ins.relation_label}\nSCORE: {[f'{s*100:.2f}' for s in ins.pred_score]}\n\n")

    with open(join(dev_analysis_outdir, "correct.txt"), "w") as f:
        for ins in sorted(pred_instances, key = lambda x: (x.doc_id, x.sentid)):
            if ins.relation_label == ins.pred_relation_label and ins.pred_relation_label != "O":
                f.write(f"DOC: {ins.doc_id}\nSENT: {' '.join(ins.sent_toks)}\nTEXT: {ins.text}\nPRED: {ins.pred_relation_label}, LABEL: {ins.relation_label}\n\n")



def eval_and_save(model, val_dataloader, val_gold_ins,  best_f1, args, label_to_eval = "Contains", tuple_level = False, save_prediction = False): 

    """
    Evaluate a trained model over validation set and save if achieves better performance 
    """


    print("\n\n---------------eval------------------\n")
    pred_instances = predict(model, val_dataloader)

    should_save = 0

    precision, recall, f1 = unary_eval(pred_instances, val_gold_ins, label_to_eval, tuple_level = tuple_level)

    score_str = f"precision: {precision*100:.2f}, recall: {recall*100:.2f}, f1: {f1*100:.2f}, best f1: {best_f1}\n"

    if best_f1 is None or f1 > best_f1:
        best_f1 = f1
        should_save = 1

    print(f"------------- Evaluation ------------\n\n{score_str}\n")

    # save model now 
    if should_save and args.save_model:

        if not os.path.exists(args.model_save_dir):
            os.makedirs(args.model_save_dir)

        print(f"\nsaving model to {args.model_save_dir}\n")
        torch.save(model.state_dict(), join(args.model_save_dir, args.model_save_name + ".ckpt"))

        # write model setting
        with open(join(args.model_save_dir, args.model_save_name + ".config"), "a") as f:
            f.write(f"{args}\n")


    if save_prediction:
            with open(join(args.model_save_dir, "spans.pred"), "wb") as f:
                pickle.dump(pred_instances, f)

    if args.analyze_dev:
            analayze(pred_instances, val_gold_ins, args.model_save_dir)
       

    return best_f1


def train(model, train_dataloader, val_dataloader, val_gold_ins, args):

    """ 
    This function trains a Containee model 

    Args:
        model:
            model to train 
        train_dataloder:
            a dataloader that contains training Containee instances 
        val_dataloder:
            a dataloader that cotnains extracted component instances from development data 
        val_gold_ins:
            a list of gold containee instances from DEV data. This is used to evaluate the model over the  development data (val_dataloader doesn't have gold labels. It only provides component instances for the model to make predictions for). 
        args:
            argument parser instance 
    """

    model.to(device)
    

    num_batches = len(train_dataloader)


    """ optimizer """
    param_optimizer = list(model.named_parameters())


    no_decay = ['bias', 'LayerNorm.bias', 'LayerNorm.weight']

    optimizer_grouped_parameters = [
               {'params': [p for n, p in param_optimizer if not any(nd in n for nd in no_decay) and p.requires_grad], 'weight_decay': 0.01},
               {'params': [p for n, p in param_optimizer if any(nd in n for nd in no_decay) and p.requires_grad ], 'weight_decay': 0.0}
          ]

    optimizer = AdamW(optimizer_grouped_parameters,
                              lr=args.lr, correct_bias=False)

    """ scheduler """
    num_training_steps = len(train_dataloader) * args.epoch
    num_warmup_steps = int(0.1 * num_training_steps)
    scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=num_warmup_steps, num_training_steps=num_training_steps)  # PyTorch scheduler

    best_f1 = None

    loss_funct = torch.nn.CrossEntropyLoss()

    for epoch in range(args.epoch):
        avg_loss = 0
        model.train()
        
        for batch_i, train_item in enumerate(train_dataloader):

            logits = model.forward(train_item)

            loss = loss_funct(logits, train_item
            ["labels"].to(device))

            stdout.write(f'\r{epoch}/{args.epoch} epoch: batch = {batch_i}/{num_batches} batch, batch loss = {loss.item():.2f}')
            stdout.flush()

            avg_loss += loss.item()

            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), args.max_grad_norm)
            
            optimizer.step()
            scheduler.step() 
        
            optimizer.zero_grad()

        print("\n\n---------------------------------\n")
        print(f"\n{epoch} epoch avg loss: {avg_loss/num_batches:.2f}\n\n")

        print("eval over val ... ")
        args.save_model = 1
        best_f1 = eval_and_save(model, val_dataloader, val_gold_ins,best_f1, args)

    print("Training ends ! \n")



if __name__ == "__main__":
    """ ================= parse =============== """
    parser = argparse.ArgumentParser()
    
    # I/O
    parser.add_argument("--train_dir", required = True, help = 'directory where extracted span instances (made by make_train_dev_test.py) are stored')

    parser.add_argument("--val_dir", required = True, help = 'directory where extracted span instances from DEV data are stored')
    
    parser.add_argument("--analyze_dev", default = 0, choices = [0,1], type = int, help = 'whether to produce analysis about the model predictions over the DEV data')

    parser.add_argument("--dropout", default = 0, type = float)
    
    parser.add_argument("--seed", help = "seed", default = 100, type = int)
    
    parser.add_argument("--epoch", help = "number epochs to train", default = 5, type = int)

    parser.add_argument("--lr", default = 0.00001, type = float)
    
    parser.add_argument("--save_model", help = "whether to save the model or not", default = 1, type = int, choices = [0,1])

    parser.add_argument("--model_save_dir", default = "saved_model", help = "where to save the model")
    
    parser.add_argument("--model_save_name", default = "trained_model", help = "name of the model to be saved")

    parser.add_argument("--batch_size", type = int, default = 10, help = "training batch size")
    
    parser.add_argument("--shuffle", type = int, default = 1, choices = [1,0], help = "whether to shuffle the training data")

    parser.add_argument("--max_grad_norm", default = 1.00, type = float, help = "max gradient norm to clip")

    args = parser.parse_args()

    args.num_classes = len(label2ind)

    seed = args.seed

    seed_everything(seed)

    ners = ['Component']

    add_marker_tokens(tokenizer, ners) # add markers into the tokenizer's vocabulary

    print("Loading data ")

    # load data, this set is a instance-level training set 
    with open(join(args.train_dir, "spanins.pkl"), "rb") as f:
        train_ins = pickle.load(f)
        pos = [r.relation_label for r in train_ins if r.relation_label != "O" ]

        print(f"Training set contains {len(pos)}/{len(train_ins)}({len(pos)/len(train_ins):.2f}) positive instances ")

    with open(join(args.val_dir, "spanins.pkl"), "rb") as f:
        val_ins = pickle.load(f)

    with open(join(args.val_dir, "gold_spanins.pkl"), "rb") as f:
        val_gold_ins = pickle.load(f)
    
    """ ================ make dataset ================ """
    print("Making dataset ... ")
    train_dataset = MyDataset(train_ins)
    val_dataset = MyDataset(val_ins)

    """ ================ make dataloader ============= """
    print("Making data loader ...")
    batch_size = args.batch_size

    train_dataloader = DataLoader(train_dataset, batch_size = args.batch_size, shuffle = args.shuffle, collate_fn = collate)

    val_dataloader = DataLoader(val_dataset, batch_size = args.batch_size, collate_fn = collate)

    """ ================ model ================ """
    model = Model(tokenizer, args)

    """ ================ train ================ """
    print("Start training ")
    train(model, train_dataloader, val_dataloader, val_gold_ins, args)

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



