from transformers import * 
import torch 
import sys
from os.path import join, dirname, abspath
curpath = dirname(abspath(__file__))
upperpath = dirname(curpath)
sys.path.append(upperpath)
from transformers import BertTokenizerFast
from config import tokenizer_type
from transformers import *
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

class REModel(torch.nn.Module):
  def __init__(self, args): 
    super(REModel, self).__init__()

    # self.width_embeddings = torch.nn.Embedding(args.max_width, args.width_dimension)
    self.model_type = tokenizer_type
    assert self.model_type in ["bert-large-uncased", "bert-large-cased", "bert-base-cased", "bert-base-uncased"]
    if self.model_type in ["bert-large-uncased", "bert-large-cased"]:
      self.encoder_dimension = 1024
    else:
      self.encoder_dimension = 768

    self.bert_encoder = AutoModel.from_pretrained(self.model_type)


    self.dropout = torch.nn.Dropout(0.1)
    self.layernorm = torch.nn.LayerNorm(self.encoder_dimension * 2)
    self.linear = torch.nn.Linear(self.encoder_dimension*2, args.num_classes)



  def forward(self, item):
      # span_starts, span_ends: torch tensor, shape = (batch,)

      # first encode 
      # last_hidden_states, pooled_outputs = self.bert_encoder.forward(sent_inputids, attention_mask = sent_attention_masks)
      # # (batch, seq, dimension)

      sent_inputids = item["sent_inputids"].to(device)
      sent_attention_masks = item["sent_attention_masks"].to(device)
      starts1 = item["starts1"].to(device)
      starts2 = item["starts2"].to(device)

      last_hidden_states = self.bert_encoder(sent_inputids, attention_mask = sent_attention_masks)[0]


      batch_size, seq_len, dimension = last_hidden_states.size() # get (batch, 2*dimension), [start_embedding, end_embedding]

     
      start_indices1 = starts1.view(batch_size, -1).repeat(1, dimension).unsqueeze(1) # (batch, 1, dimension)
      start_embeddings1 = torch.gather(last_hidden_states, 1, start_indices1).view(batch_size, -1) # shape (batch, dimension)



      start_indices2 = starts2.view(batch_size, -1).repeat(1, dimension).unsqueeze(1) # (batch, 1, dimension)
      start_embeddings2 = torch.gather(last_hidden_states, 1, start_indices2).view(batch_size, -1) # shape (batch, dimension)



      relation_embeddings = self.dropout(self.layernorm(torch.cat(( start_embeddings1, start_embeddings2), 1))) # shape = (batch, 2*dimension + dimension)

      # feed forward now
      logits = self.linear(relation_embeddings)

      return logits


