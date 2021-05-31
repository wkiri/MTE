import os, sys, argparse, torch, random, json
from transformers import *
from torch.utils.data import DataLoader
from os.path import abspath, dirname, join, exists
from sys import stdout
import numpy as np
from copy import deepcopy
from dataset import MyDataset, collate

# label info 
curpath = dirname(abspath(__file__))
upperpath = dirname(curpath)
sys.path.append(upperpath)
from config import label2ind, ind2label





device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


from tabulate import tabulate 

def predict(model, dataloader):
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
                ins.pred_relation_label = ind2label[y_pred]
                ins.pred_score = score
                pred_instances.append(ins)

    return pred_instances

  