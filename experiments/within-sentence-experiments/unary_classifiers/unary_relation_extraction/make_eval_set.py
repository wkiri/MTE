# python3
# make_eval_set.py
# Mars Target Encyclopedia
# This function makes within sentence instances and removes duplicates based on texts. 
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
shared_path = join(exppath, 'shared')
sys.path.insert(0, shared_path)

from extraction_utils import get_docid, extract_gold_relations_from_ann, extract_intrasent_goldrelations_from_ann, extract_entitypairs_from_text_file, get_offset2sentid, extract_entities_from_text, get_sentid_from_offset

from other_utils import add_marker_tokens, read_inlist 

from instance import Span_Instance, Rel_Instance

upperpath = dirname(curpath)
sys.path.append(upperpath)

from config import label2ind, ind2label,  tokenizer_type


from transformers import *

def make_instances(ann_files, text_files, corenlp_files, outdir):

    """
    This function extracts gold relation instances from gold annotation. 
    
    Args:
        ann_files:
            a list of ann files
        text_files:
            a list of text files 
        corenlp_files:
            a list of .json files that contains parsing output dictionary from CoreNLP for each text files in text_files. 
        outdir:
            output directory 
    """

    # first collect all valid entity for predictions. this is instance-based, which only relies on character offset. And it only extracts spans that cooccur with target in a sentence 
    gold_relins = [] 


    for text_file, ann_file, corenlp_file in zip(text_files, ann_files, corenlp_files):

        intrasent_gold_relations = [(e1, e2, relation) for e1, e2, relation in extract_intrasent_goldrelations_from_ann(ann_file, corenlp_file = corenlp_file) if relation == 'Contains' and e1['label'] == 'Target' and e2['label'] in ['Element', 'Mineral']]


        for e1, e2, relation in intrasent_gold_relations:
    
            span1 = Span_Instance(e1['venue'], e1['year'], e1['docname'], e1['doc_start_char'], e1['doc_end_char'], e1['text'], 'Target')
 
            span2 = Span_Instance(e2['venue'], e2['year'], e2['docname'], e2['doc_start_char'], e2['doc_end_char'], e2['text'], 'Component')

            rel = Rel_Instance(span1,span2, 'Contains')
            gold_relins.append(rel)
 
    if not exists(outdir):
        os.makedirs(outdir)

    outfile = join(outdir, f"gold_relins.pkl")
    print(f"Saving the evaluation set ({len(gold_relins)} relations) to {outfile}")
    with open(outfile, "wb") as f:
        pickle.dump(gold_relins, f)

def main(args):

    test_annfiles, test_textfiles, test_corenlpfiles = read_inlist(args.test_inlist)
    
    make_instances(test_annfiles, test_textfiles, test_corenlpfiles, args.outdir)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument('--test_inlist', required = True, help = 'Input list of test documents')

    parser.add_argument('--outdir', required = True, help = 'Output directory')

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
