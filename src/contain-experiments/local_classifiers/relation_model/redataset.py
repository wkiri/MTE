# dataset to collect enumerated spans. The BertNER model accepts this dataset and predict ner for each span. 
# NOTE: this dataset is used only for spans that needs NER predictions.  It is not used for storing the gold spans (which are used for evaluation)

from torch.utils.data import Dataset, DataLoader
import pickle, torch, json, os, sys, re
from sys import stdout
from os.path import join, exists, abspath, dirname
import numpy as np  
import random
from collections import Counter

curpath = dirname(abspath(__file__))
upperpath = dirname(curpath)
sys.path.append(upperpath)

from config import label2ind, ind2label


# VERY IMPORTANT ! WITHOUT COLLATE DATALODER WOULD OUTPUT A TRANSPOSED OUTPUT 
def re_collate(batch):
    batch_size = len(batch)
    item = {}
    # return rel.input_ids, rel.span1_bert_start, rel.span2_bert_start, rel.re_id, rel.sentence, rel.type1, rel.type2
            
    sent_inputids = [rel.input_ids for rel in batch]
    seq_lenths = torch.LongTensor(list(map(len, sent_inputids)))
    max_seq_len = seq_lenths.max()

    inputid_tensor = torch.zeros(batch_size, max_seq_len, dtype = torch.long)
    mask = torch.zeros(batch_size, max_seq_len, dtype = torch.long)

    for i, (seq, seq_len) in enumerate(zip(sent_inputids, seq_lenths)):
        inputid_tensor[i,:seq_len] = torch.LongTensor(seq)
        mask[i,:seq_len] = torch.LongTensor([1]*int(seq_len))
    item["sent_inputids"] = inputid_tensor
    item["starts1"] = torch.LongTensor([rel.span1_bert_start_idx for rel in batch])
    item["starts2"] = torch.LongTensor([rel.span2_bert_start_idx for rel in batch])
    item["sent_attention_masks"] = mask
    item["labels"] = torch.LongTensor([label2ind[rel.label] for rel in batch]) if batch[0].label is not None else torch.LongTensor([-1] * batch_size)
    item["rel_instances"] = batch

    return item 

class REDataset(Dataset):
    def __init__(self,rels):
        # sanity check that there are no duplicates in span ids
        super(Dataset, self).__init__()

        # first shuffle
        self.rels = rels 
        random.Random(100).shuffle(self.rels)

        # for r in rels:
        #     assert 0 <= r.span1_bert_start < len(r.input_ids) and 0 <= r.span2_bert_start < len(r.input_ids)


    def __len__(self):
        return len(self.rels)

    def __getitem__(self, i):
        return self.rels[i]

   


