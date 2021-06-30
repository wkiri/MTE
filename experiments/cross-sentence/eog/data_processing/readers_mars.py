#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 14/08/2019

author: fenia
"""

import os, re, sys
from collections import OrderedDict
from tqdm import tqdm
from recordtype import recordtype
from os.path import join, abspath, dirname, exists
import glob 


TextStruct = recordtype('TextStruct', 'pmid txt')
EntStruct = recordtype('EntStruct', 'pmid name off1 off2 type kb_id sent_no word_id bio')
RelStruct = recordtype('RelStruct', 'pmid type arg1 arg2')
PairStruct = recordtype('PairStruct', 'pmid type arg1 arg2 dir cross closest')


def readPubTator(infile):
    """
    Read data and store in structs
    """
    # return:
    #     abstracts, entities, relations, doc, pmid

    abstracts = OrderedDict() # # extracted relations from text file and ann files 
    entities = OrderedDict() # extracted gold entities from text file and ann files
    relations = OrderedDict()
    corenlp_files = OrderedDict()


    lines = open(infile, 'r').readlines()
    for line in tqdm(lines):
        # text. only need 'a' section 
        if len(line.rstrip().split('|')) == 3 and \
                line.strip().split('|')[1] == 'a':
            line = line.strip().split('|')

            pmid = line[0]
            text = line[2]  # .replace('>', '\n')

            if pmid not in abstracts:
                abstracts[pmid] = [TextStruct(pmid, text)]
            else:
                abstracts[pmid] += [TextStruct(pmid, text)]
        # entities
        elif len(line.rstrip().split('\t')) == 6:
            line = line.strip().split('\t')
            pmid = line[0]
            offset1 = int(line[1])
            offset2 = int(line[2])
            ent_name = line[3]
            ent_type = line[4]
            kb_id = line[5].split('|')

            # currently consider each possible ID as another entity
            for k in kb_id:
                if pmid not in entities:
                    entities[pmid] = [EntStruct(pmid, ent_name, offset1, offset2, ent_type, [k], -1, [], [])]
                else:
                    entities[pmid] += [EntStruct(pmid, ent_name, offset1, offset2, ent_type, [k], -1, [], [])]
        elif len(line.rstrip().split('\t')) == 7:
            line = line.strip().split('\t')
            pmid = line[0]
            offset1 = int(line[1])
            offset2 = int(line[2])
            ent_name = line[3]
            ent_type = line[4]
            kb_id = line[5].split('|')
            extra_ents = line[6].split('|')

            for i, e in enumerate(extra_ents):
                if pmid not in entities:
                    entities[pmid] = [EntStruct(pmid, ent_name, offset1, offset2, ent_type, [kb_id[i]], -1, [], [])]
                else:
                    entities[pmid] += [EntStruct(pmid, ent_name, offset1, offset2, ent_type, [kb_id[i]], -1, [], [])]

        # relations
        elif len(line.rstrip().split('\t')) == 4:
            line = line.strip().split('\t')
            pmid = line[0]
            rel_type = line[1]
            arg1 = tuple((line[2].split('|')))
            arg2 = tuple((line[3].split('|')))

            if pmid not in relations:
                relations[pmid] = [RelStruct(pmid, rel_type, arg1, arg2)]
            else:
                relations[pmid] += [RelStruct(pmid, rel_type, arg1, arg2)]
        elif "|<corenlpfile>:" in line:
            pmid, corenlp_file = line.strip().split("|<corenlpfile>:")
            corenlp_files[pmid] = corenlp_file
        else:
            continue

    return abstracts, entities, relations, corenlp_files