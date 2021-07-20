#!/usr/bin/env python
#
# Read in a text file, run CoreNLP to get features (pos, lemma, NER),
# and convert it to JSRE's data ("examples") format.
# Interactively solicity labels from the user.
# Note: see below for how to select whether 'elements' or 'minerals'
# will be used to generate the candidate relation pairs 
# (enables separate evaluation for these classes).
#
# Author: Kiri Wagstaff
# March 13, 2017
# Copyright notice at bottom of file.

import sys, os, io
import json
import urllib
from pycorenlp import StanfordCoreNLP

def pretty_print(json_obj):
    print json.dumps(json_obj, 
                     sort_keys=True, indent=2, separators=(',', ': '))


indirname  = '../text/lpsc15-C-raymond-sol1159'
#indirname  = '../text/lpsc15-C-raymond-jsre'
outdirname = '../text/lpsc15-C-kiri-jsre'

#indirname  = '../text/lpsc16-C-raymond'
#outdirname = '../text/lpsc16-C-kiri-jsre'

dirlist = [fn for fn in os.listdir(indirname) if
           fn.endswith('.txt')]
dirlist.sort()

corenlp = StanfordCoreNLP('http://localhost:9000')
# Specify CoreNLP properties
props = { 'annotators': 'tokenize,ssplit,lemma,pos,ner',
          'ner.model': 'ner_model_train_62r15_685k14_384k15.ser.gz',
          'outputFormat': 'json'}

print 'Processing %d documents. ' % len(dirlist)

for fn in dirlist:
    fnamebase = fn[:fn.find('.txt')]

    infname   = '%s.txt' % fnamebase
    outfname  = '%s-mineral.examples' % fnamebase

    print 'Reading in %s' % infname

    inf = open(os.path.join(indirname, infname))
    text = inf.read()
    inf.close()

    # Quote (with percent-encoding) reserved characters in URL for CoreNLP
    text = urllib.quote(text)
    doc = corenlp.annotate(text, properties=props)
    
    with io.open(os.path.join(outdirname, outfname), 'w', encoding='utf8') as outf:

        # Goal: Map Raymond's .ann (brat) annotations into the CoreNLP-parsed
        # sentence/token structure.  
        ex_id = 0
        for s in doc['sentences']:
            # For each pair of target+(element|mineral) entities,
            # are they in a contains relationship?
            # label:
            # 0 - negative
            # 1 - entity_1 contains entity_2
            # 2 - entity_2 contains entity_1
            # Get the relevant entities (Target, Element, Mineral)
            targets  = [t for t in s['tokens'] if t['ner'] == 'Target']
            elements = [t for t in s['tokens'] if t['ner'] == 'Element']
            minerals = [t for t in s['tokens'] if t['ner'] == 'Mineral']
            # Select whether to use elements or minerals
            # active = elements
            active = minerals

            '''
            print ' '.join([w['word'] for w in s['tokens']])
            print minerals
            raw_input()
            '''
          
            for i in range(len(targets)):
                for j in range(len(active)):
                    # Ideally, use "contains" brat annotations to set label
                    # For now, go interactive

                    # Print the sentence with relevant entities highlighted
                    words = [w['word'] for w in s['tokens']]
                    sent = ''
                    for w,word in enumerate(words):
                        # CoreNLP indexes starting at 1
                        if (w == targets[i]['index']-1 or
                            w == active[j]['index']-1):
                            sent += '_%s_ ' % word
                        else:
                            sent += '%s ' % word
                    print sent

                    # Solicit a label form the user
                    label = -1
                    while label not in [0,1]:
                        print 'Select one:'
                        print '0: no relationship'
                        print '1: %s contains %s' % (targets[i]['word'],
                                                     active[j]['word'])
                        label = int(raw_input())
                    # Change label from 1 to 2 if needed
                    if label != 0:
                        if targets[i]['index'] < active[j]['index']:
                            label = 1
                        else:
                            label = 2

                    # Create a unique identifier
                    id    = '%s_%s_%s' % (fnamebase,
                                          str(s['index']),
                                          str(ex_id))
                    ex_id += 1 
                    body  = ''
                    for t in s['tokens']:
                        # Target entity is the agent;
                        # Element entity is the target (of the relation)
                        if t['index'] == targets[i]['index']:
                            entity_label = 'A'
                        elif t['index'] == active[j]['index']:
                            entity_label = 'T'
                        else:
                            entity_label = 'O'

                        # CoreNLP indexes starting at 1
                        body += '%d&&%s&&%s&&%s&&%s&&%s ' % (t['index']-1,
                                                             t['word'],
                                                             t['lemma'],
                                                             t['pos'],
                                                             t['ner'],
                                                             entity_label)
                    # Output the example
                    print '%s\t%s\t%s\n' % (label, id, body)
                    outf.write('%s\t%s\t%s\n' % (label, id, body))
                    print


# Copyright 2017, by the California Institute of Technology. ALL
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

