#!/usr/bin/env python
# 
# Read in brat .ann file[s] and report summary statistics:
# - Histogram of entity types
# - Histogram of relation types
# - Number of sentence-crossing relations
#
# Author: Kiri Wagstaff
# April 19, 2017
# Copyright notice at bottom of file.

import sys, os
# The following two lines make CoreNLP happy
reload(sys)
sys.setdefaultencoding('UTF8')
import json
import urllib
from pycorenlp import StanfordCoreNLP
from brat_annotation import BratAnnotation
import itertools

def pretty_print(json_obj):
    print json.dumps(json_obj, 
                     sort_keys=True, indent=2, separators=(',', ': '))

#indirname  = '../corpus-LPSC/lpsc15-C-raymond-sol1159'
#indirname  = '../corpus-LPSC/lpsc15-C-raymond-sol1159-v2'
indirname  = '../corpus-LPSC/lpsc15-C-raymond-sol1159-v3-utf8'
#indirname  = '../corpus-LPSC/lpsc16-C-raymond'
#indirname  = '../corpus-LPSC/lpsc16-C-raymond-sol1159-utf8'

dirlist = [fn for fn in os.listdir(indirname) if
           fn.endswith('.txt') and len(fn) == 8]  # assume ????.txt
dirlist.sort()

corenlp = StanfordCoreNLP('http://localhost:9000')
# Specify CoreNLP properties
props = { 'annotators': 'ssplit',
          #'ner.model': 'ner_model_train_63r15v2_685k14-no-ref_384k15-no-ref.ser.gz',
          'ner.model': 'ner_62r15v3_emt_gazette.ser.gz',
          'outputFormat': 'json'}

print 'Processing %d documents. ' % len(dirlist)

# Get the sentence index for the specific annotation.
# Return -1 if not found.
def get_sentence(ann, doc):
    # If ann contains multiple tokens, need to find them one by one
    sp = ann.name.split()
    if len(sp) > 1:
        firstword = sp[0]
    else:
        firstword = ann.name
    for s in doc['sentences']:
        for (i,t) in enumerate(s['tokens']):
            # Note CoreNLP is 0-indexed but brat is 1-indexed
            # Also allow for annotations that are substrings of 
            # CoreNLP tokens.  (Won't work for superstrings.)
            if (t['characterOffsetBegin'] <= int(ann.start)-1 and
                t['characterOffsetEnd']   >= int(ann.start)+len(firstword)-1 and
                firstword in t['word']):
                if len(sp) == 1:
                    #print ann.name, t['word'], s['index']
                    return s['index']
                # if ann is multi-token then keep checking
                if len(sp) > 1:
                    mismatch = False
                    for (j,w) in enumerate(sp[1:]):
                        # Strip off any final punctuation
                        w = w.strip('.')
                        ptr = i+1+j
                        tok = s['tokens'][ptr]
                        if (w not in tok['word']):
                            mismatch = True
                            break;
                    if mismatch == False:
                        #print ann.name, t['word'], s['index']
                        return s['index']
    return -1
    
crossing = 0
total_rels = 0
for fn in dirlist:
    fnamebase = fn[:fn.find('.txt')]

    infname  = '%s.txt' % fnamebase
    bratname = '%s.ann' % fnamebase

    # Read in the text file
    print 'Reading in %s' % infname

    inf = open(os.path.join(indirname, infname))
    text = inf.read()
    inf.close()

    # Read in the annotations (brat) file
    anns = []
    with open(os.path.join(indirname, bratname), 'r') as f:
        for line in f.readlines():
            anns += [BratAnnotation(line, fnamebase, 'raymond')]

    # Print out counts for each type (label)
    labels = [a.label for a in anns]
    for l in sorted(list(set(labels))):
        print '%s:\t%d' % (l, len([a for a in anns if a.label == l]))
    print
    for r in ['anchor', 'relation', 'event']:
        r_labels = [a.label for a in anns if a.type == r]
        print '%s: ' % r
        for l in sorted(list(set(r_labels))):
            print '%s:\t%d' % (l, len([a for a in anns if 
                                       a.type == r and a.label == l]))
        print

    # Process text with CoreNLP to split by sentences
    # Quote (with percent-encoding) reserved characters in URL for CoreNLP
    text = urllib.quote(text)
    doc = corenlp.annotate(text, properties=props)
    #pretty_print(doc)

    # For each 'contains' relation (actually an event), 
    # does it cross sentences?
    events  = [a for a in anns if a.type == 'event' and a.label == 'Contains']
    anchors = [a for a in anns if a.type == 'anchor']
    for e in events:
        # Each event expresses a many-to-many relation between
        # targets and components.  Use itertools to get all possible combos.
        rels = list(itertools.product(e.targets, e.cont))

        # For each relation, get the sentence indices for its target and cont
        for (tg,ct) in rels:
            tg_ann = [t for t in anchors if t.annotation_id == tg][0]
            tg_s_id = get_sentence(tg_ann, doc)
            if tg_s_id == -1:
                print 'Error: could not find %s.' % tg_ann.name
                continue
                #sys.exit(1)

            ct_ann = [c for c in anchors if c.annotation_id == ct][0]
            ct_s_id = get_sentence(ct_ann, doc)
            if ct_s_id == -1:
                print 'Error: could not find %s.' % ct_ann.name
                continue
                #sys.exit(1)

            if tg_s_id != ct_s_id:
                crossing += 1
            total_rels += 1

    print '%d / %d (%.2f%%) relations cross sentences.' % \
        (crossing, total_rels, 
         crossing*100.0/total_rels if total_rels > 0 else 0)



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
