# python3
# other_utils.py
# Mars Target Encyclopedia
#
# Yuan Zhuang
# July 30, 2021
# Copyright notice at bottom of file.



import sys, os, re
from os.path import exists 

def read_inlist(file):
    with open(file, "r") as f:
        lines = f.read().strip().split("\n")
    files = [] 
    for line in lines:
        line = line.strip()
        if line == '': continue
        ann_file, text_file, corenlp_file = line.split(",")
        if not ann_file.endswith(".ann"):
            raise NameError(f'Invalid ann file: {ann_file}')
        if not text_file.endswith(".txt"):
            raise NameError(f"Invalid text file: {text_file}")
        if not corenlp_file.endswith(".txt.json"):
            raise NameError(f"Invalid corenlp file: {corenlp_file}")
        files.append((ann_file, text_file, corenlp_file))

    ann_files, text_files, corenlp_files = zip(*files)

    for k in ann_files + text_files + corenlp_files:
        if not exists(k):
            raise NameError(f"FILE does not exists: {k}")

    return ann_files, text_files, corenlp_files

def add_marker_tokens(tokenizer, ner_labels):
    new_tokens = []
    for label in ner_labels:
        new_tokens.append('<ner_start=%s>'%label.lower())
        new_tokens.append('<ner_end=%s>'%label.lower())
    tokenizer.add_tokens(new_tokens)


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