#!/usr/bin/env python3
# Read in brat .ann files and convert to CoreNLP's NER CRF format.
#
# Author: Steven Lu
# Copyright notice at bottom of file.

# from pycorenlp import StanfordCoreNLP
import os, sys, argparse, json, re, copy
from os import makedirs, listdir
from os.path import exists, join, abspath
from sys import stdout

from parse_annot_configs import accept_ner_labels as accept_labels


def convert(text_file, ann_file, stanford_file, stanford_has_ner_prediction):



    text, tree = parse(text_file, ann_file)


    output = json.load(open(stanford_file, "r"))

    compare_tree = copy.deepcopy(tree)
    for s in output["sentences"]:
        tokens = [t for t in s['tokens']]
        include_brat_ann(tokens, compare_tree)

    records = []
    # for sentence in output['sentences']:
    for sentid, sentence in enumerate(output["sentences"]):
        if sentid != 42:
            continue
        continue_ann, continue_ann_en = None, None
        # for tok in sentence['tokens']:
        for tok in sentence["tokens"]:
            # begin, tok_end = tok['characterOffsetBegin'], tok['characterOffsetEnd']
            begin, tok_end = tok["characterOffsetBegin"], tok["characterOffsetEnd"]
            label = 'O' # annotated ner label
            if stanford_has_ner_prediction:
                predicted_ner = tok["ner"] if tok["ner"] in accept_labels else "O" # predicted ner label from trained ner model

            if begin in tree:
                node = tree[begin]
                if len(node) > 1:
                    print("WARN: multiple starts at ", begin, node)
                    if tok_end in node:
                        node = {tok_end: node[tok_end]} # picking one
                        print("Chose:", node)
                
                ann_end, labels = list(node.items())[0]
                if not len(labels) == 1:
                    print("WARN: Duplicate labels for token: %s, label:%s. Using the first one!" % (tok['word'], str(labels)))
                # if accept_labels is not None and labels[0] in accept_labels:
                #     label = labels[0]
                if tok_end == ann_end: # annotation ends where token ends
                    continue_ann = None
                elif tok_end < ann_end and label != 'O':
                    print("Continue for the next %d chars" % (ann_end - tok_end))
                    continue_ann = label
                    continue_ann_end = ann_end
            elif continue_ann is not None and tok_end <= continue_ann_end:
                print("Continuing the annotation %s, %d:%d %d]" % (continue_ann, begin, tok_end, continue_ann_end))
                label = continue_ann            # previous label is this label
                if continue_ann_end == tok_end: # continuation ends here
                    print("End")
                    continue_ann = None
            else:
                continue_ann, continue_ann_end, continue_ann_begin = None, None, None


            if stanford_has_ner_prediction:
                print(f"{tok['word']}\t{tok['lemma']}\t{label}\t{predicted_ner}\t{tok['characterOffsetBegin']}\t{tok['characterOffsetEnd']}\t{1 if continue_ann is not None else 0}")
            else:
                print(f"{tok['word']}\t{label}\t{tok['characterOffsetBegin']}\t{tok['characterOffsetEnd']}\t{1 if continue_ann is not None else 0}")



def parse(txt_file, ann_file):
    with open(txt_file) as text_file, open(ann_file) as ann_file:
        texts = text_file.read()
        text_file.close()

        anns = map(lambda x: x.strip().split('\t'), ann_file)
        anns = filter(lambda x: len(x) > 2, anns)
        # FIXME: ignoring the annotatiosn which are complex

        anns = filter(lambda x: ';' not in x[1], anns)
        # FIXME: some annotations' spread have been split into many, separated by ; ignoring them

        def __parse_ann(ann):
            spec = ann[1].split()
            name = spec[0]
            markers = list(map(lambda x: int(x), spec[1:]))
            #t = ' '.join([texts[begin:end] for begin,end in zip(markers[::2], markers[1::2])])
            t = texts[markers[0]:markers[1]]
            if not t == ann[2]:
                print("Error: Annotation mis-match, file=%s, ann=%s" % (txt_file, str(ann)))
                return None
            return (name, markers, t)
        anns = map(__parse_ann, anns) # format
        anns = filter(lambda x: x, anns) # skip None

        # building a tree index for easy accessing
        tree = {}
        for entity_type, pos, name in anns:
            begin, end = pos[0], pos[1]
            if begin not in tree:
                tree[begin] = {}
            node = tree[begin]
            if end not in node:
                node[end] = []
            node[end].append(entity_type)

        # Re-read file in without decoding it
        text_file = open(txt_file)
        texts = text_file.read()
        text_file.close()
        return texts, tree



def include_brat_ann(entities, brat_tree):
    continue_ann, continue_ann_end, continue_ann_begin = None, None, None
    for e in entities:
        e_begin, e_end = e['characterOffsetBegin'], e['characterOffsetEnd']
        label = 'O'
        if e_begin in brat_tree:
            node = brat_tree[e_begin]
            if len(node) > 1:
                #print("WARN: multiple starts at ", e_begin, node)
                if e_end in node:
                    #e['ann_id'] = node[e_end][0]  # picking one
                    node = {e_end: node[e_end]}  # picking one
                    #print("Chose:", node)
            ann_end, labels = list(node.items())[0]
            if not len(labels) == 1:
                print("WARN: Duplicate ids for token: %s, id:%s. Using the first one!" % (e['word'], str(labels)))
            label = labels[0]
            if e_end == ann_end:  # annotation ends where token ends
                continue_ann = None
            elif e_end < ann_end and label != 'O':
                #print("Continue for the next %d chars" % (ann_end - e_end))
                continue_ann = label
                continue_ann_end = ann_end
                continue_ann_begin = e_begin
        elif continue_ann is not None and e_end <= continue_ann_end and e_begin > continue_ann_begin:
            #print("Continuing the annotation %s, %d:%d %d]" % (continue_ann, e_begin, e_end, continue_ann_end))
            label = continue_ann  # previous label is this label
            if continue_ann_end == e_end:  # continuation ends here
                continue_ann = None
        else:
            continue_ann, continue_ann_end, continue_ann_begin = None, None, None
        if label != 'O':
            e['ann_id'] = label


text_file = "../data/corpus-LPSC/mpf-reviewed+properties-v2/1998_1534.txt"
ann_file = "../data/corpus-LPSC/mpf-reviewed+properties-v2/1998_1534.ann"
stanford_file = "../data/stanford-parse-with-ner/corpus-LPSC/mpf-reviewed+properties-v2/1998_1534.txt.json"
stanford_has_ner_prediction = 1

convert(text_file, ann_file, stanford_file, stanford_has_ner_prediction)


