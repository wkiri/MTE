#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on %(date)s

@author: fenia
"""

import os
import sys
import re
from recordtype import recordtype
from networkx.algorithms.components.connected import connected_components
from itertools import combinations
import numpy as np
from collections import OrderedDict
from utils import to_graph, to_edges, using_split2
from tqdm import tqdm
sys.path.append('./common/genia-tagger-py/')
from geniatagger import GENIATagger

pwd = '/'.join(os.path.realpath(__file__).split('/')[:-1])

genia_splitter = os.path.join("./common", "geniass")
genia_tagger = GENIATagger(os.path.join("./common", "genia-tagger-py", "geniatagger-3.0.2", "geniatagger"))


TextStruct = recordtype('TextStruct', 'pmid txt')
EntStruct = recordtype('EntStruct', 'pmid name off1 off2 type kb_id sent_no word_id bio')
RelStruct = recordtype('RelStruct', 'pmid type arg1 arg2')
PairStruct = recordtype('PairStruct', 'pmid type arg1 arg2 dir cross closest')


def generate_pairs(uents, type1, type2, true_rels):
    """
    Generate pairs (both positive & negative):
    Type1 - Type2 should have 1-1 association, e.g. [A, A] [B, C] --> (A,B), (A,C)
    Args:
        uents:
        type1: (list) with entity semantic types
        type2: (list) with entity semantic types
        true_rels:
    """
    pairs = OrderedDict()
    combs = combinations(uents, 2)

    unk = 0
    total_rels = len(true_rels)
    found_rels = 0

    for c in combs:
        # all pairs
        diff = 99999

        target = []
        for e1 in uents[c[0]]:
            for e2 in uents[c[1]]:
                # find most close pair to each other
                if e1.word_id[-1] <= e2.word_id[0]:
                    if abs(e2.word_id[0] - e1.word_id[-1]) < diff:
                        target = [e1, e2]
                        diff = abs(e2.word_id[0] - e1.word_id[-1])
                else:
                    if abs(e1.word_id[0] - e2.word_id[-1]) < diff:
                        target = [e1, e2]
                        diff = abs(e2.word_id[0] - e1.word_id[-1])

        if target[0].word_id[-1] <= target[1].word_id[0]:  # A before B (in text)
            a1 = target[0]
            a2 = target[1]
        else:                                              # B before A (in text)
            a1 = target[1]
            a2 = target[0]

        if c[0][0].startswith('UNK:') or c[1][0].startswith('UNK:'):  # ignore non-grounded entities
            continue

        cross_res = find_cross(c, uents)
        not_found_rels = 0

        for tr in true_rels:

            # AB existing relation
            if list(set(tr.arg1).intersection(set(c[0]))) and list(set(tr.arg2).intersection(set(c[1]))):
                for t1, t2 in zip(type1, type2):
                    if uents[c[0]][0].type == t1 and uents[c[1]][0].type == t2:
                        pairs[(c[0], c[1])] = \
                            PairStruct(tr.pmid, '1:' + tr.type + ':2', c[0], c[1], 'L2R', cross_res, (a1, a2))
                        found_rels += 1

            # BA existing relation
            elif list(set(tr.arg1).intersection(set(c[1]))) and list(set(tr.arg2).intersection(set(c[0]))):
                for t1, t2 in zip(type1, type2):
                    if uents[c[1]][0].type == t1 and uents[c[0]][0].type == t2:
                        pairs[(c[1], c[0])] = \
                            PairStruct(tr.pmid, '1:'+tr.type+':2', c[1], c[0], 'R2L', cross_res, (a2, a1))
                        found_rels += 1

            # relation not found
            else:
                not_found_rels += 1

        # this pair does not have a relation
        if not_found_rels == total_rels:
            for t1, t2 in zip(type1, type2):
                if uents[c[0]][0].type == t1 and uents[c[1]][0].type == t2:
                    pairs[(c[0], c[1])] = PairStruct(a1.pmid, '1:NR:2', c[0], c[1], 'L2R', cross_res, (a1, a2))
                    unk += 1
                elif uents[c[1]][0].type == t1 and uents[c[0]][0].type == t2:
                    pairs[(c[1], c[0])] = PairStruct(a1.pmid, '1:NR:2', c[1], c[0], 'R2L', cross_res, (a2, a1))
                    unk += 1

    assert found_rels == total_rels, '{} <> {}, {}, {}'.format(found_rels, total_rels, true_rels, pairs)

    # # Checking
    # if found_rels != total_rels:
    #     print('NON-FOUND RELATIONS: {} <> {}'.format(found_rels, total_rels))
    #     for p in true_rels:
    #         if (p.arg1, p.arg2) not in pairs:
    #             print(p.arg1, p.arg2)
    return pairs

def find_cross(pair, unique_ents):
    """
    Find if the pair is in cross or non-cross sentence.
    Args:
        pair: (tuple) target pair
        unique_ents: (dic) entities based on grounded IDs
    Returns: (str) cross/non-cross
    """
    non_cross = False
    for m1 in unique_ents[pair[0]]:
        for m2 in unique_ents[pair[1]]:
            if m1.sent_no == m2.sent_no:
                non_cross = True
    if non_cross:
        return 'NON-CROSS'
    else:
        return 'CROSS'


def fix_sent_break(sents, entities):
    """
    Fix sentence break + Find sentence of each entity
    Args:
        sents: (list) sentences
        entities: (recordtype)
    Returns: (list) sentences with fixed sentence breaks
    """
    sents_break = '\n'.join(sents)

    for e in entities:
        if '\n' in sents_break[e.off1:e.off2]:
            sents_break = sents_break[0:e.off1] + sents_break[e.off1:e.off2].replace('\n', ' ') + sents_break[e.off2:]
    return sents_break.split('\n')


def find_mentions(entities):
    """
    Find unique entities and their mentions
    Args:
        entities: (dic) a struct for each entity
    Returns: (dic) unique entities based on their grounded ID, if -1 ID=UNK:No
    """
    equivalents = []
    for e in entities:
        if e.kb_id not in equivalents:
            equivalents.append(e.kb_id)

    # mention-level data sets
    g = to_graph(equivalents)
    cc = connected_components(g)

    unique_entities = OrderedDict()
    unk_id = 0
    for c in cc:
        if tuple(c)[0] == '-1':
            continue
        unique_entities[tuple(c)] = []

    # consider non-grounded entities as separate entities
    for e in entities:
        if e.kb_id[0] == '-1':
            unique_entities[tuple(('UNK:' + str(unk_id),))] = [e]
            unk_id += 1
        else:
            for ue in unique_entities.keys():
                if list(set(e.kb_id).intersection(set(ue))):
                    unique_entities[ue] += [e]

    return unique_entities


def sentence_split_genia(tabst):
    """
    Sentence Splitting Using GENIA sentence splitter
    Args:
        tabst: (list) title+abstract

    Returns: (list) all sentences in abstract
    """
    os.chdir(genia_splitter)

    with open('temp_file.txt', 'w') as ofile:
        for t in tabst:
            ofile.write(t+'\n')
    os.system('./geniass temp_file.txt temp_file.split.txt > /dev/null 2>&1')

    split_lines = []
    with open('temp_file.split.txt', 'r') as ifile:
        for line in ifile:
            line = line.rstrip()
            if line != '':
                split_lines.append(line.rstrip())
    os.system('rm temp_file.txt temp_file.split.txt')
    os.chdir(pwd)
    return split_lines


def tokenize_genia(sents):
    """
    Tokenization using Genia Tokenizer
    Args:
        sents: (list) sentences

    Returns: (list) tokenized sentences
    """
    token_sents = []
    for i, s in enumerate(sents):
        tokens = []

        for word, base_form, pos_tag, chunk, named_entity in genia_tagger.tag(s):
            tokens += [word]

        text = []
        for t in tokens:
            if t == "'s":
                text.append(t)
            elif t == "''":
                text.append(t)
            else:
                text.append(t.replace("'", " ' "))

        text = ' '.join(text)
        text = text.replace("-LRB-", '(')
        text = text.replace("-RRB-", ')')
        text = text.replace("-LSB-", '[')
        text = text.replace("-RSB-", ']')
        text = text.replace("``", '"')
        text = text.replace("`", "'")
        text = text.replace("'s", " 's")
        text = text.replace('-', ' - ')
        text = text.replace('/', ' / ')
        text = text.replace('+', ' + ')
        text = text.replace('.', ' . ')
        text = text.replace('=', ' = ')
        text = text.replace('*', ' * ')
        if '&amp;' in s:
            text = text.replace("&", "&amp;")
        else:
            text = text.replace("&amp;", "&")

        text = re.sub(' +', ' ', text).strip()  # remove continuous spaces

        if "''" in ''.join(s):
            pass
        else:
            text = text.replace("''", '"')

        token_sents.append(text)
    return token_sents


def get_new_offset(old_off1, old_off2, oldoffset2newoffset):
    # oldoffset2newoffset is maps tok boundary from old offset to new offset 

    new_off1 = None 
    new_off2 = None 
    for (old_start, old_end), (new_start, new_end) in oldoffset2newoffset.items():
        if old_off1 == old_start:
                new_off1 = new_start 
        if old_off2 == old_end:
                new_off2 = new_end 
    assert new_off1 is not None and new_off2 is not None 
    return new_off1, new_off2

def adjust_offsets(entities, doc):
    new_sents = [ ' '.join([tok['word'] for tok in sent['tokens']]) for sent in doc['sentences']]
    newtext = "".join(new_sents)

    # change entities' offset to match the new sents 
    oldoffset2newoffset = {} 
    newoffset2sentno = {}
    
    curlen = 0 
    for i, sent in enumerate(doc['sentences']):
        for tok_id, tok in enumerate(sent['tokens']):
            cur_start = tok['characterOffsetBegin']
            cur_end = tok['characterOffsetEnd']
            if tok_id == 0:
                new_start = curlen
            else:
                new_start = curlen + 1 # adding space 
            new_end = new_start + len(tok['word'])
            curlen = new_end

            oldoffset2newoffset[(cur_start, cur_end)] = (new_start, new_end)
            newoffset2sentno[new_start] = i 

    for e in entities:
        e.off1, e.off2 = get_new_offset(e.off1, e.off2, oldoffset2newoffset)

    new_entities = []
    terms = {}
    for e in entities:
        start = e.off1
        end = e.off2

        if (start, end) not in terms:
            terms[(start, end)] = [[start, end, e.type, e.name, e.pmid, e.kb_id]]
        else:
            terms[(start, end)].append([start, end, e.type, e.name, e.pmid, e.kb_id])

    flatten_toks = [ (tok['word'], tok['characterOffsetBegin'], tok['characterOffsetEnd']) for sent in doc['sentences'] for tok in sent['tokens']]

    for ts in terms.values(): # doc start char, doc end char, to, term(start, end, e.type, e.name, e.pmid, e.kb_id)
        for term in ts:
            """ Convert to word Ids """
            span2append = []
            tag = term[2] # ner label f
            # tokid, tok text, tok start char in sent, tok end char in sent 
            sent_no = newoffset2sentno[term[0]]
            for tok_id, (tok, start, end) in enumerate(flatten_toks):
                # start = int(start)
                # end = int(end)
                start, end = oldoffset2newoffset[(start, end)]
                if (start, end) == (term[0], term[1]):
                    span2append.append(tok_id)

                elif start == term[0] and end < term[1]:

                    span2append.append(tok_id)

                elif start > term[0] and end < term[1]:

                    span2append.append(tok_id)

                elif start > term[0] and end == term[1] and (start != end):
                    span2append.append(tok_id)

                elif len(set(range(start, end)).intersection(set(range(term[0], term[1])))) > 0:
                    span2append.append(tok_id)

            new_entities += [EntStruct(term[4], newtext[term[0]:term[1]], term[0], term[1], term[2], term[5],
                                       sent_no, span2append, None)]

    return new_entities, newoffset2sentno, oldoffset2newoffset, new_sents

