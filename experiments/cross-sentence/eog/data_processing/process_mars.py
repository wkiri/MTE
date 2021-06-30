#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on %(date)s

@author: fenia
"""

import os, glob, json
from os.path import join 
import re
from tqdm import tqdm
from recordtype import recordtype
from collections import OrderedDict
import argparse
import pickle
from itertools import permutations, combinations
from tools_mars import adjust_offsets, find_mentions, find_cross, generate_pairs
from readers_mars import *

TextStruct = recordtype('TextStruct', 'pmid txt')
EntStruct = recordtype('EntStruct', 'pmid name off1 off2 type kb_id sent_no word_id bio')
RelStruct = recordtype('RelStruct', 'pmid type arg1 arg2')


def generate_data(infile, outdir, dataname):
    assert dataname in ['train','dev','test']

    if not os.path.exists(outdir):
        os.makedirs(outdir)
    positive, negative = 0, 0

    with open(join(outdir, f"{dataname}.data"), 'w') as data_out:

        abstracts, entities, relations, corenlp_files = readPubTator(infile)
        type1 = ['Target']
        type2 = ['Component']

        pbar = tqdm(list(abstracts.keys()))
        for i in pbar:
            # Process 
            # adjust offsets
            # added by yuan 
            corenlp_file = corenlp_files[i]
            doc = json.load(open(corenlp_file, "r"))
            new_entities, newoffset2sentno, oldoffset2newoffset, new_sentstrs = adjust_offsets(entities[i], doc) # need to adjust sents to reflect the entities offset. need to consider how to achieve it without adding spaces


            ''' Find mentions '''
            unique_entities = find_mentions(new_entities)

            ''' Generate Pairs '''
            if i in relations:
                pairs = generate_pairs(unique_entities, type1, type2, relations[i])
            else:
                pairs = generate_pairs(unique_entities, type1, type2, [])   # generate only negative pairs


            # 'pmid type arg1 arg2 dir cross'
            data_out.write('{}\t{}'.format(i, '|'.join(new_sentstrs)))

            for args_, p in pairs.items():
                if p.type != '1:NR:2':
                    positive += 1
                elif p.type == '1:NR:2':
                    negative += 1
                
                data_out.write('\t{}\t{}\t{}\t{}-{}\t{}-{}'.format(p.type, p.dir, p.cross, p.closest[0].word_id[0],p.closest[0].word_id[-1]+1, p.closest[1].word_id[0], p.closest[1].word_id[-1]+1))

                data_out.write('\t{}\t{}\t{}\t{}\t{}\t{}'.format(
                    '|'.join([g for g in p.arg1]),
                    '|'.join([e.name for e in unique_entities[p.arg1]]),
                    unique_entities[p.arg1][0].type,
                    ':'.join([str(e.word_id[0]) for e in unique_entities[p.arg1]]),
                    ':'.join([str(e.word_id[-1] + 1) for e in unique_entities[p.arg1]]),
                    ':'.join([str(e.sent_no) for e in unique_entities[p.arg1]])))

                data_out.write('\t{}\t{}\t{}\t{}\t{}\t{}'.format(
                    '|'.join([g for g in p.arg2]),
                    '|'.join([e.name for e in unique_entities[p.arg2]]),
                    unique_entities[p.arg2][0].type,
                    ':'.join([str(e.word_id[0]) for e in unique_entities[p.arg2]]),
                    ':'.join([str(e.word_id[-1] + 1) for e in unique_entities[p.arg2]]),
                    ':'.join([str(e.sent_no) for e in unique_entities[p.arg2]])))
            data_out.write('\n')
    print('Total positive pairs:', positive)
    print('Total negative pairs:', negative)
    print(f"Saving to {join(outdir, f'{dataname}.data')}")


def main():
    """ 
    Main processing function 
    """
    train_infile = "../data/mars/train.txt"
    dev_infile = "../data/mars/dev.txt"
    test_infile = "../data/mars/test.txt"
    outdir = "../data/mars/processed"


    generate_data(train_infile, outdir, 'train')
    generate_data(dev_infile, outdir, 'dev')
    generate_data(test_infile, outdir, 'test')
    
if __name__ == "__main__":
    main()
