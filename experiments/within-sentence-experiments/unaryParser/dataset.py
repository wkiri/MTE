# python3
# dataset.py
# Mars Target Encyclopedia
# This script contains the customized torch dataset. 
#
# Yuan Zhuang
# July 30, 2021
# Copyright notice at bottom of file.

from torch.utils.data import Dataset, DataLoader
import pickle, torch, json, os, sys, re
from sys import stdout
from os.path import join, exists, abspath, dirname
import numpy as np  
import random
from collections import Counter
from config import label2ind, ind2label 

def pad_seqs(seqs, tensor_type):
      # each seq should be a list of numbers
      # pad each seq to same length 

      # used to pad 
      batch_size = len(seqs)

      seq_lenths = torch.LongTensor(list(map(len, seqs)))
      max_seq_len = seq_lenths.max()

      seq_tensor = torch.zeros(batch_size, max_seq_len, dtype = tensor_type)

      mask = torch.zeros(batch_size, max_seq_len, dtype = torch.long)

      for i, (seq, seq_len) in enumerate(zip(seqs, seq_lenths)):
        seq_tensor[i,:seq_len] = torch.tensor(seq, dtype = tensor_type)
        mask[i,:seq_len] = torch.LongTensor([1]*int(seq_len))
      return seq_tensor, mask


def collate(batch):
    
    batch_size = len(batch)

    item = {}

    sent_inputids, sent_attention_masks = pad_seqs([ins.input_ids for ins in batch], torch.long)
    item["sent_inputids"] = sent_inputids
    item["sent_attention_masks"] = sent_attention_masks
    item["span_widths"] = torch.LongTensor([ins.span_width - 1  for ins in batch])


    item["bert_starts"] = torch.LongTensor([ins.bert_start_idx for ins in batch])
    item["bert_ends"] = torch.LongTensor([ins.bert_end_idx for ins in batch])

    item["labels"] = torch.LongTensor([label2ind[ins.relation_label] for ins in batch]) if batch[0].relation_label is not None else torch.LongTensor([-1] * batch_size)
    item["instances"] = batch

    return item 

class MyDataset(Dataset):
    def __init__(self,instances):

        super(Dataset, self).__init__()

        # first shuffle
        self.instances = instances
        random.Random(100).shuffle(self.instances)

    def __len__(self):
        return len(self.instances)

    def __getitem__(self, i):
        return self.instances[i]

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


