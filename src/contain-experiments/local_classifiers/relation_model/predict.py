import os, sys, argparse, torch, random, json
from transformers import *
from torch.utils.data import DataLoader
from os.path import abspath, dirname, join, exists
from sys import stdout
import numpy as np
from copy import deepcopy

# label info 
curpath = dirname(abspath(__file__))
upperpath = dirname(curpath)
sys.path.append(upperpath)
from config import label2ind, ind2label

from redataset import REDataset, re_collate

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
            
            # test_input_ids,test_attention_masks, test_start_tensors1, test_start_tensors2,  test_re_ids, test_texts, test_types1, test_types2 = item[:8]
            stdout.write(f"\rpredicting {i}/{len(dataloader)}")
            stdout.flush()

            logits =model.forward(item)
            scores = soft(logits).cpu().numpy()

            y_preds = np.argmax(scores,1)

            for rel, y_pred, score in zip(item["rel_instances"], y_preds, scores):
                rel.pred_relation_label = ind2label[y_pred]
                rel.pred_score = score
                pred_instances.append(rel)

    return pred_instances

  