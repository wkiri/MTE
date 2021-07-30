# python3
# make_train_dev_test.py
# Mars Target Encyclopedia
# This script makes within-sentence container examples for training, development and test set.
#
# Yuan Zhuang
# July 30, 2021
# Copyright notice at bottom of file.

import re, pickle, sys, argparse, random, json, os
from sys import stdout
from copy import deepcopy 
from os.path import abspath, dirname, join, exists
from os import makedirs, listdir

curpath = dirname(abspath(__file__))

exppath = dirname(dirname(dirname(curpath)))
sharedpath = join(exppath, 'shared')
sys.path.insert(0, sharedpath)

from instance import Span_Instance

from extraction_utils import get_docid, extract_gold_entities_from_ann,extract_intrasent_entitypairs_from_text_file, extract_intrasent_goldrelations_from_ann, extract_entities_from_text, get_offset2sentid, get_sentid_from_offset

from other_utils import read_inlist, add_marker_tokens

upperpath = dirname(curpath)
sys.path.append(upperpath)
from config import label2ind, ind2label,  tokenizer_type


from transformers import *



def make_instances( tokenizer, ann_files, text_files, corenlp_files, outdir, max_len = 512, is_training = False, use_sys_ners = False):

    """
    This function extract training, dev and testing target instances from files

    Args:
        tokenizer: 
            a bert tokenizer 
        ann_files: 
            a list of ann files ( used to assign gold labels (binary label for whether the instance is a Container instance) to target instances)
        text_files:
            a list of text files where target instances would be extracted 
        corenlp_files:
            a list of files that store the parsing results of text files from CoreNLP.
        outdir:
            output directory to save the extracted instances 
        max_len:
            an integer to indicate the maximum number of tokens to keep for a sentence after bert tokenization (bert allows a list of input tokens with <= 512 tokens )
        is_training:
            boolean to indicate whether the extracted instances are used for training or not. 
        use_sys_ners: 
            boolean to indicate whether system ners instead of gold ners should be used to extract the target instances. 

    """

    # first collect all valid entity for predictions. this is instance-based, which only relies on character offset. And it only extracts spans that cooccur with target in a sentence
    gold_spanins = [] # stores entities that are in a gold relation in annotation. used for evaluation 

    seen_goldids = set()
    for text_file, ann_file, corenlp_file in zip(text_files, ann_files, corenlp_files):

        intrasent_gold_relations = [(e1, e2, relation) for e1, e2, relation in extract_intrasent_goldrelations_from_ann(ann_file, corenlp_file = corenlp_file) if relation == 'Contains' and e1['label'] == 'Target' and e2['label'] in ['Element', 'Mineral']]

        for e1, e2, relation in intrasent_gold_relations:
            span1 = Span_Instance(e1['venue'], e1['year'], e1['docname'], e1['doc_start_char'], e1['doc_end_char'], e1['text'], 'Target')
            span1.relation_label = 'Contains'
            
            if span1.span_id not in seen_goldids:
                seen_goldids.add(span1.span_id)
                gold_spanins.append(span1)

    spanins = []
    seen_spanids = set()
    exceed_len_cases = 0 
    added_extra = 0 
    pseudo_positive_training = []
    for text_file, ann_file, corenlp_file in zip(text_files, ann_files, corenlp_files):

        doc = json.load(open(corenlp_file))

        for e1, e2 in extract_intrasent_entitypairs_from_text_file(text_file, ann_file, doc = doc, use_sys_ners = use_sys_ners, use_component = True):

            sentid = e1['sentid']
            if e1['label'] != 'Target' or e2['label'] not in ['Element', 'Mineral', 'Component']:
                continue

            sent_toks = [token['word'] for token in doc['sentences'][sentid]['tokens']]
    

            span1 = Span_Instance(e1['venue'], e1['year'], e1['docname'], e1['doc_start_char'], e1['doc_end_char'], e1['text'], 'Target', sent_toks = deepcopy(sent_toks), sentid = sentid, sent_start_idx = e1['sent_start_idx'], sent_end_idx = e1['sent_end_idx'])

            if span1.span_id not in seen_spanids:
                exceed = span1.insert_type_markers(tokenizer, max_len = max_len)
                span1.relation_label = 'Contains' if span1.span_id in seen_goldids else 'O'
                spanins.append(span1)
                seen_spanids.add(span1.span_id)
                exceed_len_cases += exceed
            
        if is_training:
            posins_ids = set([(s.venue, s.year, s.docname, s.sentid, s.std_text) for s in spanins if s.relation_label != 'O'])
            
            for s in spanins:
                if (s.venue, s.year, s.docname, s.sentid, s.std_text) in posins_ids:

                    if s.relation_label == 'O':
                        pseudo_positive_training.append(s)
                    s.relation_label = 'Contains'

    print(f"Generated {len(spanins)} extracted instances with {len([s for s in spanins if s.relation_label != 'O'])} positive, and {exceed_len_cases} of these exceed max_len")
    
    print(f"Generated {len(gold_spanins)} gold instances")

    intersection = len(set([s.span_id for s in spanins]).intersection(seen_goldids))/len(seen_goldids)
    print(f"{intersection*100:.2f}% gold spans are matched in the extracted spans")
            
    if not exists(outdir):
        os.makedirs(outdir)

    outfile = join(outdir, f"spanins.pkl")
    print(f"Saving to {outfile}")
    with open(outfile, "wb") as f:
        pickle.dump(spanins, f)

    outfile = join(outdir, f"gold_spanins.pkl")
    print(f"Saving the evaluation set to {outfile}")
    with open(outfile, "wb") as f:
        pickle.dump(gold_spanins, f)

    print()

def main(args):
    tokenizer = BertTokenizerFast.from_pretrained(tokenizer_type)

    add_marker_tokens(tokenizer, ['Target'])

    train_annfiles, train_textfiles, train_corenlpfiles = read_inlist(args.train_inlist)
    print(f"Making Train data from {len(train_annfiles)} files")

    outdir = join(curpath, "ins/train")
    make_instances(tokenizer, train_annfiles, train_textfiles, train_corenlpfiles, outdir, max_len = args.max_len, is_training = True, use_sys_ners = False)

    dev_annfiles, dev_textfiles, dev_corenlpfiles = read_inlist(args.dev_inlist)
    print(f"Making DEV data from {len(dev_annfiles)} files")
    outdir = join(curpath, "ins/dev/gold_ner")
    make_instances( tokenizer, dev_annfiles, dev_textfiles, dev_corenlpfiles, outdir, max_len = args.max_len, use_sys_ners = False)

    test_annfiles, test_textfiles, test_corenlpfiles = read_inlist(args.test_inlist)
    print(f"Making TEST data from {len(test_annfiles)} files")
    outdir = join(curpath, "ins/test/gold_ner")
    make_instances( tokenizer, test_annfiles, test_textfiles, test_corenlpfiles, outdir, max_len = args.max_len, use_sys_ners = False)


    vocab_dir = join(curpath, 'ins')
    tokenizer.save_vocabulary(vocab_dir)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument('--train_inlist', required = True, help = "input list of files for TRAIN data. Each line is in the format of '<ann_file>,<text_file>,<corenlp_file>' where <corenlp_file> is the json file that stores the parsing results of the text file using CoreNLP. ")

    parser.add_argument('--dev_inlist', required = True, help = "input list of files for DEV data. It is in the same format as train_inlist ")

    parser.add_argument('--test_inlist', required = True, help = "input list of files for TEST data.  It is in the same format as train_inlist ")

    parser.add_argument('--max_len', type = int, default = 512, help = "maximum number of tokens in a sentence encoded by BERT")


    args = parser.parse_args()
    main(args)

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
