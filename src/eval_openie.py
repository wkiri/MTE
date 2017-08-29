#!/usr/bin/env python
# eval_openie.py
# Evaluate OpenIE extractions for the MTE corpus.
# 1. Read in OpenIE annotations (relations) and NER detections.
# 2. Filter OpenIE relations to only those with Element, Mineral, or Target NER tags.
# 3. Compare remaining relations to MTE database "contains" content.
#
# Kiri Wagstaff
# November 3, 2016
# Copyright notice at bottom of file.

import sys, os
import glob
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter


def main(args):

    # 1. Read in OpenIE annotations (relations) and NER detections.
    rels = []
    for f in glob.glob('%s/*.txt' % args['openie']):
        with open(f,'r') as inf:
            lines = inf.readlines()
            in_rels = False
            for l in lines:
                if l.startswith('Extracted the following Open IE triples:'):
                    in_rels = True
                    continue
                if l.startswith('Sentence'): # end of extractions
                    in_rels = False
                    continue
                if not in_rels:
                    continue

                # Format: confidence NP_1 rel NP_2
                rels += [l.strip().split('\t')]
    print 'Found %d relations.' % len(rels)

    ner_elements = []
    ner_minerals = []
    ner_targets  = []
    for f in glob.glob('%s/*.txt' % args['ner']):
        with open(f,'r') as inf:
            lines = inf.readlines()
            for l in lines:
                if l.startswith('['):
                    # Format: Text CharacterOffsetBegin CharacterOffsetEnd PartOfSpeech Lemma NamedEntityTag
                    vals = l[1:-2].split()
                    if 'NamedEntityTag=Element' in vals:
                        ner_elements += [vals[0].split('=')[1]]
                    elif 'NamedEntityTag=Mineral' in vals:
                        ner_minerals += [vals[0].split('=')[1]]
                    elif 'NamedEntityTag=Target' in vals:
                        ner_targets += [vals[0].split('=')[1]]
    print 'Found %d NER elements.' % len(ner_elements)
    print 'Found %d NER minerals.' % len(ner_minerals)
    print 'Found %d NER targets.'  % len(ner_targets)

    # 2. Filter OpenIE relations to only those with Element, Mineral, or Target NER tags.
    for r in rels:
        (conf, np1, rel, np2) = r
        np1_words = np1.split()
        np2_words = np1.split()
        if ((np1 in ner_targets and (any(e in np2_words for e in ner_elements) or
                                     any(m in np2_words for m in ner_minerals))) or
            (np2 in ner_targets and (any(e in np1_words for e in ner_elements) or
                                     any(m in np1_words for m in ner_minerals)))):
            print '%s, %s, %s' % (np1, rel, np2)

    # 3. Compare remaining relations to MTE database "contains" content.


if __name__ == '__main__':
    parser = ArgumentParser(description='Evaluate OpenIE extractions against MTE DB',
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("-openie", help="Directory containing OpenIE output files", required=True)
    parser.add_argument("-ner", help="Directory containing NER output files", required=True)
    parser.add_argument("-db", help="database name for insertion", default='mte')
    parser.add_argument("-user", help="DB user name", default=os.environ['USER'])
    args = vars(parser.parse_args())

    main(args)


# Copyright 2016, by the California Institute of Technology. ALL
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
