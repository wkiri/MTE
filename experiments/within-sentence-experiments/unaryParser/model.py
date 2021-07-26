from transformers import * 
import torch, sys, logging 
logging.basicConfig(level = logging.DEBUG)

from os.path import join, dirname, abspath
from transformers import *
from model_utils import to_device, add_marker_tokens

class Model(torch.nn.Module):
  def __init__(self, model_name, gpu_id = 0): 
    """
    Args:
      model_name: either Container or Containee
      gpu_id: denote the GPU device to use. Negative gpu_id indicates not using any gpu
    """
    super(Model, self).__init__()

    self.model_type = 'bert-base-uncased'
    self.model_name = model_name
    
    self.gpu_id = gpu_id
    if self.gpu_id < 0: 
      logging.info(f'GPU is not used due to negative GPU ID {self.gpu_id}.')


    self.tokenizer = BertTokenizerFast.from_pretrained(self.model_type)

    if self.model_name == 'Containee':
      add_marker_tokens(self.tokenizer, ['Component'])
    elif self.model_name == 'Container':
      add_marker_tokens(self.tokenizer, ['Target'])
    else:
      logging.error(f'Unrecognized model name: {self.model_name}')

    self.bert_encoder = AutoModel.from_pretrained(self.model_type)
    self.bert_encoder.resize_token_embeddings(len(self.tokenizer))
    
    self.encoder_dimension = 768
    self.layernorm = torch.nn.LayerNorm(self.encoder_dimension * 3)
    self.linear = torch.nn.Linear(self.encoder_dimension * 3, 2)


  def forward(self, item):
      
      sent_inputids = to_device(item["sent_inputids"], self.gpu_id)
      sent_attention_masks = to_device(item["sent_attention_masks"],  self.gpu_id)
      starts1 = to_device(item["bert_starts"],  self.gpu_id)
      ends1 = to_device(item["bert_ends"],  self.gpu_id)

      last_hidden_states, cls_embds = self.bert_encoder(sent_inputids, attention_mask = sent_attention_masks)

      batch_size, seq_len, dimension = last_hidden_states.size() # get (batch, 2*dimension), [start_embedding, end_embedding]

      start_indices1 = starts1.view(batch_size, -1).repeat(1, dimension).unsqueeze(1)# (batch, 1, dimension)
      start_embeddings1 = torch.gather(last_hidden_states, 1, start_indices1).view(batch_size, -1) # shape (batch, dimension)

      end_indices1 = ends1.view(batch_size, -1).repeat(1, dimension).unsqueeze(1) # (batch, 1, dimension) 
      end_embeddings1 = torch.gather(last_hidden_states, 1, end_indices1).view(batch_size, -1) # shape (batch, dimension)
      
      logits =  self.linear(self.layernorm(torch.cat((start_embeddings1, end_embeddings1, cls_embds), 1)))


      return logits
  


