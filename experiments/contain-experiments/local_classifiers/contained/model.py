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
  def __init__(self, args): 
    super(Model, self).__init__()

    # self.width_embeddings = torch.nn.Embedding(args.max_width, args.width_dimension)
    self.model_type = tokenizer_type
    assert self.model_type in ["bert-large-uncased", "bert-large-cased", "bert-base-cased", "bert-base-uncased"]
    if self.model_type in ["bert-large-uncased", "bert-large-cased"]:
      self.encoder_dimension = 1024
    else:
      self.encoder_dimension = 768
    # width_dim = 100
    # self.width_embds = torch.nn.Embedding(args.max_span_width, width_dim)

    self.bert_encoder = AutoModel.from_pretrained(self.model_type)

    # self.linear = torch.nn.Linear(self.encoder_dimension * , args.num_classes)
    # self.layernorm = torch.nn.LayerNorm(self.encoder_dimension * 3)
    

    self.dropout = torch.nn.Dropout(0.2)
    self.linear = torch.nn.Linear(self.encoder_dimension * 3, args.num_classes)




   


  def forward(self, item):
      # span_starts, span_ends: torch tensor, shape = (batch,)

      # first encode 
      # last_hidden_states, pooled_outputs = self.bert_encoder.forward(sent_inputids, attention_mask = sent_attention_masks)
      # # (batch, seq, dimension)

      sent_inputids = item["sent_inputids"].to(device)
      sent_attention_masks = item["sent_attention_masks"].to(device)
      starts1 = item["bert_starts"].to(device)
      ends1 = item["bert_ends"].to(device)
      span_widths = item["span_widths"].to(device)

      # width_embds = self.width_embds(span_widths)

      last_hidden_states, cls_embds = self.bert_encoder(sent_inputids, attention_mask = sent_attention_masks)


      batch_size, seq_len, dimension = last_hidden_states.size() # get (batch, 2*dimension), [start_embedding, end_embedding]

     
      start_indices1 = starts1.view(batch_size, -1).repeat(1, dimension).unsqueeze(1)# (batch, 1, dimension)
      start_embeddings1 = torch.gather(last_hidden_states, 1, start_indices1).view(batch_size, -1) # shape (batch, dimension)

      end_indices1 = ends1.view(batch_size, -1).repeat(1, dimension).unsqueeze(1) # (batch, 1, dimension) 
      end_embeddings1 = torch.gather(last_hidden_states, 1, end_indices1).view(batch_size, -1) # shape (batch, dimension)

     
      
      # drop the whole embedding randomly 
      embd_idx = torch.ones(3).to(device)
      dropped_weights = self.dropout(embd_idx).view(3,-1).repeat(1,dimension).view(-1) # 3, dimension 
      dropped_embds = torch.multiply(torch.cat((start_embeddings1, end_embeddings1, cls_embds), 1), dropped_weights)  
      logits = self.linear(dropped_embds)


      # logits = self.linear(self.dropout(torch.cat((start_embeddings1, end_embeddings1, cls_embds), 1)))

      return logits


