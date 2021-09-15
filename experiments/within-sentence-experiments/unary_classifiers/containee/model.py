# python3
# model.py
# Mars Target Encyclopedia
# This script contains codes for Containee model. 
#
# Yuan Zhuang
# July 30, 2021
# Copyright notice at bottom of file.

from transformers import * 
import torch 
import sys
from os.path import join, dirname, abspath

curpath = dirname(abspath(__file__))
upperpath = dirname(curpath)
sys.path.append(upperpath)
from config import tokenizer_type

from transformers import *
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class Model(torch.nn.Module):
  def __init__(self, tokenizer, args): 
    super(Model, self).__init__()

    self.model_type = tokenizer_type
    assert self.model_type in ["bert-large-uncased", "bert-large-cased", "bert-base-cased", "bert-base-uncased"]
    
    if self.model_type in ["bert-large-uncased", "bert-large-cased"]:
      self.encoder_dimension = 1024
    else:
      self.encoder_dimension = 768


    self.bert_encoder = AutoModel.from_pretrained(self.model_type)
    self.tokenizer = tokenizer

    # change vocabulary by adding markers
    self.bert_encoder.resize_token_embeddings(len(tokenizer))

    self.layernorm = torch.nn.LayerNorm(self.encoder_dimension * 3)

    self.linear = torch.nn.Linear(self.encoder_dimension * 3, 2)

   


  def forward(self, item):

      sent_inputids = item["sent_inputids"].to(device)

      sent_attention_masks = item["sent_attention_masks"].to(device)

      starts1 = item["bert_starts"].to(device)

      ends1 = item["bert_ends"].to(device)

      span_widths = item["span_widths"].to(device)

      last_hidden_states, cls_embds = self.bert_encoder(sent_inputids, attention_mask = sent_attention_masks)

      batch_size, seq_len, dimension = last_hidden_states.size() # get (batch, 2*dimension), [start_embedding, end_embedding]

      start_indices1 = starts1.view(batch_size, -1).repeat(1, dimension).unsqueeze(1)# (batch, 1, dimension)
      start_embeddings1 = torch.gather(last_hidden_states, 1, start_indices1).view(batch_size, -1) # shape (batch, dimension)

      end_indices1 = ends1.view(batch_size, -1).repeat(1, dimension).unsqueeze(1) # (batch, 1, dimension) 
      end_embeddings1 = torch.gather(last_hidden_states, 1, end_indices1).view(batch_size, -1) # shape (batch, dimension)
      
      logits =  self.linear(self.layernorm(torch.cat((start_embeddings1, end_embeddings1, cls_embds), 1)))

      return logits


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

