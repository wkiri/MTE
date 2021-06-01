# relation instance over text level
import re, sys, random, os 
from os.path import abspath, dirname
from copy import deepcopy
from config import ner2markers
curpath = dirname(abspath(__file__))
sys.path.append(dirname(curpath))

from my_name_utils import canonical_target_name, canonical_elemin_name


def get_input_ids(tokenizer, toks, max_len = 512):
    tokidx2bertidx = [] #token idx to (leftmost wordpiece index in input_ids, rightmost wordpiece index in input_ids) (left = inclusive, right = exclusive)
    input_ids = [tokenizer.convert_tokens_to_ids([tokenizer.cls_token])[0]]
    for i, tok in enumerate(toks):
            
        ids = tokenizer.encode(tok, add_special_tokens = False)
        if len(input_ids) + len(ids) + 1 > max_len:
            break
        tokidx2bertidx.append([len(input_ids), len(input_ids) + len(ids)])
            
        input_ids.extend(ids)
    input_ids.append(tokenizer.convert_tokens_to_ids([tokenizer.sep_token])[0])
    return input_ids, tokidx2bertidx

def truncate(temp_prespan_ids, temp_posspan_ids, num_cut):
    # this function truncates previous and pos-context iteratively for  num_cut times . NOTE, the ids are assume to come with [CLS] and [SEP], and the truncation would not touch these two tokens
    prespan_ids = temp_prespan_ids[:]
    posspan_ids = temp_posspan_ids[:]

    while num_cut and (len(prespan_ids) > 1 or len(posspan_ids) > 1):

        if len(prespan_ids) > 1:
            prespan_ids.pop(1)
            num_cut -= 1

        if num_cut == 0:
            break
        if len(posspan_ids) > 1:
            posspan_ids.pop(-2)
            num_cut -= 1
        if num_cut == 0:
            break
    return prespan_ids, posspan_ids, num_cut

class Span_Instance:
    def __init__(self, venue, year, docname, doc_start_char, doc_end_char, text, ner_label, sent_toks = None, sentid = None, sent_start_idx = None, sent_end_idx = None):

        self.venue = venue 
        self.year = year 
        self.docname = docname

        self.doc_id = f"{venue}_{year}_{docname}"
        self.span_id = f"{self.doc_id}-{doc_start_char}-{doc_end_char}"
        self.doc_start_char = doc_start_char
        self.doc_end_char = doc_end_char
        self.text = text
        self.ner_label = ner_label
        self.std_text = canonical_target_name(self.text) if self.ner_label == "Target" else canonical_elemin_name(self.text)
        self.sent_toks = sent_toks
        self.sentid = sentid
        self.sent_start_idx = sent_start_idx
        self.sent_end_idx = sent_end_idx
        self.span_width = len(self.text.split())
        self.bert_start_idx = None # location of < of <e>
        self.bert_end_idx = None

        self.relation_label = None


    def insert_type_markers(self, tokenizer, use_std_text = True, max_len = 512):
        assert self.sent_toks is not None
        # things to get 
        self.input_ids = []
        self.span_bert_start = -1
        self.span_bert_end = -1

        success = True # whether insering type markers is successful

        # get sentence input ids
        input_ids, tokidx2bertidx = get_input_ids(tokenizer, self.sent_toks, max_len = max_len)

        # check if the spans of entity1 and entit2 exceed the range of max_len after tokenization
        if self.sent_end_idx > len(tokidx2bertidx):
            success = False
            return success


        # note that input_ids contain cls token and sep token 
        self.bert_start_idx = tokidx2bertidx[self.sent_start_idx][0]
        self.bert_end_idx = tokidx2bertidx[self.sent_end_idx - 1][-1]
        prespan_ids = input_ids[:self.bert_start_idx]
        posspan_ids = input_ids[self.bert_end_idx:]

        spanids = tokenizer.encode(self.std_text, add_special_tokens = False) if use_std_text else input_ids[self.bert_start_idx:self.bert_end_idx]


        typemarker = ner2markers[self.ner_label]
        start_type_marker = f"<{typemarker}>"
        end_type_marker = f"</{typemarker}>"
        start_marker_ids = tokenizer.encode(start_type_marker, add_special_tokens = False)
        end_marker_ids = tokenizer.encode(end_type_marker, add_special_tokens = False)

        new_inputids = prespan_ids + start_marker_ids + spanids + end_marker_ids + posspan_ids 
        
        # max_len = 10
        # prespan_ids = [0, 1,2,3,4,5,6,7,8,9]
        # posspan_ids = [10,11,12,13,14,15,16, -1]
        # diff = len(prespan_ids + posspan_ids) - max_len
        
        if len(new_inputids) > max_len:
            diff = len(new_inputids) - max_len
            # truncate now 
            # truncate right side first  

            prespan_ids, posspan_ids, diff = truncate(prespan_ids, posspan_ids, diff)

            if diff > 0:
                success = False
                return success

            new_inputids = prespan_ids + start_marker_ids + spanids + end_marker_ids + posspan_ids 


        self.bert_start_idx = len(prespan_ids)

        self.bert_end_idx = len(prespan_ids + start_marker_ids + spanids + end_marker_ids)
        self.input_ids = new_inputids

        return success



    def __str__(self):
        return f"doc_id: {self.doc_id}\ntext: {self.text}, std text: {self.std_text}, nerlabel:{self.ner_label}, involved in relation:{self.relation_label}, ({self.doc_start_char}, {self.doc_end_char}), sentid: {self.sentid}\nsentence:{'' if self.sent_toks is None else ' '.join(self.sent_toks) }\nstart end: ({self.doc_start_char, self.doc_end_char})\n"

class Rel_Instance:
    def __init__(self,span1, span2, label_str = None):

        self.span1 = span1
        self.span2 = span2
        self.re_id = f"{self.span1.span_id}|{self.span2.span_id}"
        self.label = label_str        
        self.make_signature() # self.signature is used for evaluation 

    def make_signature(self):

        self.signature = f"{self.span1.doc_id}:{self.span1.std_text},{self.span2.std_text}"


    def insert_type_markers(self, tokenizer, max_len = 512):
        # function to insert type markers around entity1 and entity2 within a sentence 

        # things to get 
        self.input_ids = []
        self.span1_bert_start_idx = -1
        self.span1_bert_end_idx = -1
        self.span2_bert_start_idx = -1
        self.span2_bert_end_idx = -1

        success = 1 # whether insering type markers is successful

        # sanity check if two entities belong to the same sentence
        if self.span1.sentid != self.span2.sentid:
            success = 0
            return success

        if self.span1.sent_toks is None and self.span2.sent_toks is None:
            success = 0
            raise NameError("Inserting type markers requires either entities has the attribute 'sent_toks'!")
            return success

        # get sentence input ids
        input_ids, tokidx2bertidx = get_input_ids(tokenizer, self.span1.sent_toks, max_len = max_len)

        # check if the spans of entity1 and entit2 exceed the range of max_len after tokenization
        if self.span1.sent_end_idx > len(tokidx2bertidx) or self.span2.sent_end_idx > len(tokidx2bertidx):
            success = 0
            return success

        #find span_bert_start_idx and span_bert_end_idx of each entity in the tokenized sentence
        span1_bert_start_idx = tokidx2bertidx[self.span1.sent_start_idx][0]
        span1_bert_end_idx = tokidx2bertidx[self.span1.sent_end_idx - 1][-1]
        span2_bert_start_idx = tokidx2bertidx[self.span2.sent_start_idx][0]
        span2_bert_end_idx = tokidx2bertidx[self.span2.sent_end_idx - 1][-1]

        # now start to insert type markers
        subj_start_marker = f"<S:{ner2markers[self.span1.ner_label]}>"
        subj_end_marker = f"</S:{ner2markers[self.span1.ner_label]}>"
        obj_start_marker = f"<O:{ner2markers[self.span2.ner_label]}>"
        obj_end_marker = f"</O:{ner2markers[self.span2.ner_label]}>"

        subj_sids, subj_eids, obj_sids, obj_eids = [ tokenizer.encode(k, add_special_tokens = False) for k in [subj_start_marker, subj_end_marker, obj_start_marker, obj_end_marker]]

        if len(subj_sids) + len(subj_eids) + len(obj_sids) + len(obj_eids) + len(input_ids) > max_len:
            diff = len(subj_sids) + len(subj_eids) + len(obj_sids) + len(obj_eids) + len(input_ids) - max_len

            prespan_end = min(span1_bert_start_idx, span2_bert_start_idx)

            posspan_start = max(span1_bert_end_idx, span2_bert_end_idx)

            prespan_ids = input_ids[:prespan_end]
            posspan_ids = input_ids[posspan_start:]
            midspan_ids = input_ids[prespan_end:posspan_start]

            new_prespan_ids, new_posspan_ids, diff = truncate(prespan_ids, posspan_ids, diff) 

            if diff > 0:
                success = 0 
                return success
            
            # modify span1_bert_start_idx, ... 
            shrink_length = len(prespan_ids) - len(new_prespan_ids)
            span1_bert_start_idx -= shrink_length
            span2_bert_start_idx -= shrink_length
            span1_bert_end_idx -= shrink_length
            span2_bert_end_idx -= shrink_length
            input_ids = new_prespan_ids + midspan_ids + new_posspan_ids

        sorted_loc = sorted([(span1_bert_start_idx,span1_bert_end_idx, "subj_start", "subj_end"), (span2_bert_start_idx, span2_bert_end_idx, "obj_start", "obj_end")], key = lambda x: x[0])
        
        queue = [sorted_loc[0][0], sorted_loc[0][1], sorted_loc[1][0], sorted_loc[1][1]]
        names = [sorted_loc[0][2], sorted_loc[0][3], sorted_loc[1][2], sorted_loc[1][3]]

        new_inputids = []
        for i, k  in enumerate(input_ids):
            if len(queue) and i == queue[0]:
                while len(queue) and i == queue[0]:
                    if names[0] == "subj_start": 
                        span1_bert_start_idx = len(new_inputids) 

                        new_inputids.extend(subj_sids)
                        new_inputids.append(k)
                    elif names[0] == "subj_end":
                        new_inputids.extend(subj_eids)
                        span1_bert_end_idx = len(new_inputids)
                        new_inputids.append(k)
                    elif names[0] == "obj_start":
                        span2_bert_start_idx = len(new_inputids)
                        new_inputids.extend(obj_sids)
                        new_inputids.append(k)
                    else:
                        new_inputids.extend(obj_eids)
                        span2_bert_end_idx = len(new_inputids)
                        new_inputids.append(k)
                    queue.pop(0)
                    names.pop(0)
            else:
                new_inputids.append(k)
        
        self.input_ids = new_inputids
        self.span1_bert_start_idx = span1_bert_start_idx
        self.span2_bert_start_idx = span2_bert_start_idx
        self.span1_bert_end_idx = span1_bert_end_idx
        self.span2_bert_end_idx = span2_bert_end_idx
        
        assert all([k >= 0 for k in [self.span1_bert_start_idx, self.span2_bert_start_idx, self.span1_bert_end_idx, self.span2_bert_end_idx]])

        left_bracket_id = tokenizer.encode("<", add_special_tokens = False)[0]
        right_bracket_id = tokenizer.encode(">", add_special_tokens = False)[0]

        assert self.input_ids[self.span1_bert_start_idx] == left_bracket_id 

        assert self.input_ids[self.span2_bert_start_idx] == left_bracket_id 
        
        assert self.input_ids[self.span1_bert_end_idx - 1] == right_bracket_id 
        
        assert self.input_ids[self.span2_bert_end_idx - 1] == right_bracket_id
        
        return success

    def __str__(self):
        sentence = " ".join(self.span1.sent_toks) if self.span1.sent_toks is not None else ""

        string = f"DOCID   :{self.span1.doc_id}\nsentence:{sentence}\nTEXT    : {self.span1.text}, {self.span2.text}\nSTD TEXT: {self.span1.std_text}, {self.span2.std_text}\nSIG: {self.signature}\nspan1:{self.span1}\nspan2:{self.span2}\n"
        
        return string