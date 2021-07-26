# relation instance over text level
import re, sys, random, os 
from os.path import abspath, dirname
from copy import deepcopy

from extraction_utils import canonical_target_name, canonical_component_name


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
        """ 
        This class is designed to store information for an entity such as Target, Element and Component

        Args:
            venue: 
                venue of the document 
            year: 
                year of the document 
            docname: 
                document name of the document 
            doc_start_char: 
                starting character offset of the entity in the document 
            doc_end_char:
                ending character offset of the entity in the document 
            text:
                text of the entity 
            ner_label: 
                ner label of the entity 
            sent_toks:
                list of words of the sentence that contains the entity 
            sentid:
                sent index of the sentence that contains the entity 
            sent_start_idx:
                the starting word index of the entity in the sentence
            sent_end_idx:
                the ending word index of the entity in the sentence
        """
    
        self.venue = venue 
        self.year = year 
        self.docname = docname

        self.doc_id = f"{venue}_{year}_{docname}"
        self.span_id = f"{self.doc_id}-{doc_start_char}-{doc_end_char}"
        self.doc_start_char = doc_start_char
        self.doc_end_char = doc_end_char
        self.text = text
        self.ner_label = ner_label
        self.std_text = canonical_target_name(self.text) if self.ner_label == "Target" else canonical_component_name(self.text)
        self.sent_toks = sent_toks
        self.sentid = sentid
        self.sent_start_idx = sent_start_idx
        self.sent_end_idx = sent_end_idx
        self.span_width = len(self.text.split())
        self.bert_start_idx = None # location of < of <e>
        self.bert_end_idx = None

        self.relation_label = None


    def insert_type_markers(self, tokenizer, use_std_text = True, max_len = 512):
        """
            This function inserts type markers such as <Target> around the entity in the sentence 

            use_std_text: whether to substitute the entity's text with its canonical name in the sentence. for example, 
            if use_std_text is true, then the sentence 'A contains K' would be turned into 'A contains <T>Potassium<\\T>'
        """
        assert self.sent_toks is not None


        self.input_ids = []
        exceed_leng = 0 

        prespans = tokenizer.tokenize(" ".join(["[CLS]"] + self.sent_toks[:self.sent_start_idx]))
        start_markers = [f"<ner_start={self.ner_label.lower()}>"]
        if use_std_text:
            spans = tokenizer.tokenize(self.std_text)
        else:
            spans = tokenizer.tokenize(" ".join(self.sent_toks[self.sent_start_idx:self.sent_end_idx]))

        end_markers = [f"<ner_end={self.ner_label.lower()}>"]

        posspans = tokenizer.tokenize(' '.join(self.sent_toks[self.sent_end_idx:] + ["[SEP]"]))

        if len(prespans + start_markers + spans + end_markers + posspans) > max_len:
            # truncate now 
            diff = len(prespans + start_markers + spans + end_markers + posspans) - max_len

            prepsans, posspans, diff = truncate(prespans, posspans, diff)

        self.input_ids = tokenizer.convert_tokens_to_ids(prespans + start_markers + spans + end_markers + posspans)
        self.bert_start_idx = len(prespans)
        self.bert_end_idx = len(prespans + start_markers + spans)


        assert tokenizer.convert_ids_to_tokens(self.input_ids)[self.bert_start_idx] == f"<ner_start={self.ner_label.lower()}>" and  tokenizer.convert_ids_to_tokens(self.input_ids)[self.bert_end_idx] == f"<ner_end={self.ner_label.lower()}>"

        # if input_ids is longger than the maximum length, simply use the 0th vector to represent the entity 
        if len(self.input_ids) > max_len:
            exceed_leng = 1
            self.input_ids = self.input_ids[: max_len]
            
            if self.bert_start_idx >= max_len:
                self.bert_start_idx = 0
            
            if self.bert_end_idx >= max_len:
                self.bert_end_idx = 0
        
        return exceed_leng



    def __str__(self):
        return f"doc_id: {self.doc_id}\ntext: {self.text}, std text: {self.std_text}, ner_label:{self.ner_label}, involved in relation:{self.relation_label}, ({self.doc_start_char}, {self.doc_end_char}), sentid: {self.sentid}\nsentence:{'' if self.sent_toks is None else ' '.join(self.sent_toks) }\nstart end: ({self.doc_start_char, self.doc_end_char})\n"

class Rel_Instance:
    def __init__(self,span1, span2, label_str = None):

        """
            This is a class to store information of a relation. A relation instance contains two entities, denotd as span1 and span2 

            Args:
                span1: 
                    target span instance
                span2: 
                    component span instance 
                label_str: 
                    relation label such as 'Contains' and 'O'
        """
        self.span1 = span1
        self.span2 = span2
        self.re_id = f"{self.span1.span_id}|{self.span2.span_id}"
        self.label = label_str        
        self.make_signature() # self.signature is used for tuple-level evaluation 

    def make_signature(self):

        self.signature = f"{self.span1.doc_id}:{self.span1.std_text},{self.span2.std_text}"


    def __str__(self):
        sentence = " ".join(self.span1.sent_toks) if self.span1.sent_toks is not None else ""

        string = f"DOCID   :{self.span1.doc_id}\nsentence:{sentence}\nTEXT    : {self.span1.text}, {self.span2.text}\nSTD TEXT: {self.span1.std_text}, {self.span2.std_text}\nSIG: {self.signature}\nspan1:{self.span1}\nspan2:{self.span2}\n"
        
        return string