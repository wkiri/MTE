#!/usr/bin/env python
#
# Read in a text file, run CoreNLP to get features (pos, lemma, NER),
# and convert it to JSRE's data ("examples") format.
#
# Authors: Kiri Wagstaff, Karanjeet Singh, Steven Lu
# Created on: September 30, 2021
# Copyright notice at bottom of file

import os
import io
import sys
import json
import urllib
from tqdm import tqdm
from pycorenlp import StanfordCoreNLP
from brat_annotation_sqlite import BratDocument


def init_corenlp(corenlp_url):
    props = {
        'annotators': 'tokenize,ssplit,lemma,pos,ner',
        'outputFormat': 'json',
        'ner.useSUTime': False,
        'ner.applyNumericClassifiers': False,
        'timeout': '60000',
        'ner.applyFineGrained': False
    }

    corenlp = StanfordCoreNLP(corenlp_url)

    return corenlp, props


def has_item_of_interest(sentence, brat_ann, accept_entity_types):
    # Keep only entity annotations in the accepted entity types
    entity_ann = [ann for ann in brat_ann if ann.label in accept_entity_types]

    for token in sentence['tokens']:
        offset_begin = token['characterOffsetBegin']
        offset_end = token['characterOffsetEnd']
        word = token['originalText']

        for ann in entity_ann:
            if ann.start == offset_begin and ann.end == offset_end and \
                    ann.name == word:
                return True

    return False


def has_relation(sentence, brat_doc, relation_type):
    # The sentence doesn't have relation if the entire document doesn't have
    # relation
    relation_ann = [ann for ann in brat_doc.ann_content
                    if ann.label.lower() == relation_type]

    if len(relation_ann) == 0:
        return False

    sentence_start = sentence['tokens'][0]['characterOffsetBegin']
    sentence_end = sentence['tokens'][-1]['characterOffsetEnd']

    for rel_ann in relation_ann:
        entity1 = brat_doc.get_ann_by_id(rel_ann.arg1)
        entity2 = brat_doc.get_ann_by_id(rel_ann.arg2)

        if entity1.start >= sentence_start and entity2.end <= sentence_end:
            return True

    return False


def generate_examples(example_id, sentence, brat_doc, relation_type,
                      accept_entity_types):
    # Keep only entity annotations in the accepted entity types
    entity_ann = [ann for ann in brat_doc.ann_content
                  if ann.label in accept_entity_types]

    # 1 means positive example, and 0 means negative example
    example_label = 0
    example_body = ''

    if has_relation(sentence, brat_doc, relation_type):
        example_label = 1

    for token in sentence['tokens']:
        offset_begin = token['characterOffsetBegin']
        offset_end = token['characterOffsetEnd']
        word = token['originalText']

        jsre_entity_type = 'O'
        jsre_entity_label = 'O'
        for ann in entity_ann:
            if ann.start == offset_begin and ann.end == offset_end and \
                    ann.name == word and ann.label == 'Target':
                jsre_entity_label = 'A'
                break
            elif ann.start == offset_begin and ann.end == offset_end and \
                ann.name == word and (ann.label == 'Element' or
                                      ann.label == 'Mineral' or
                                      ann.label == 'Property'):
                jsre_entity_label = 'T'
                break

        example_body += '%d&&%s&&%s&&%s&&%s&&%s ' % (token['index'] - 1,
                                                     token['word'],
                                                     token['lemma'],
                                                     token['pos'],
                                                     jsre_entity_type,
                                                     jsre_entity_label)

    example = '%s\t%s\t%s\n' % (example_label, example_id, example_body)

    return example


def main(relation_type, in_dir, out_dir, corenlp_url):
    if not os.path.exists(in_dir) or not os.path.isdir(in_dir):
        print '[ERROR] in_dir does not exist or is not a directory'
        sys.exit(1)

    # Create output directory
    if not os.path.exists(out_dir):
        print 'Creating output directory: %s' % os.path.abspath(out_dir)
        os.mkdir(out_dir)

    # Initialize corenlp
    corenlp, props = init_corenlp(corenlp_url)

    # Figure out entity types
    accept_entity_types = ['Target']
    if relation_type.lower() == 'contains':
        accept_entity_types.append('Element')
        accept_entity_types.append('Mineral')
    else:
        accept_entity_types.append('Property')
    print 'Accepted entity types: %s' % json.dumps(accept_entity_types)

    # Get a list of all text documents
    in_files = [fn for fn in os.listdir(in_dir) if fn.endswith('.txt')]
    in_files.sort()
    print 'Number of documents to process: %d' % len(in_files)

    for fn in tqdm(in_files, desc='Create jSRE examples', leave=True):
        fn_base = fn[: fn.find('.txt')]
        txt_fn = os.path.join(in_dir, '%s.txt' % fn_base)
        ann_fn = os.path.join(in_dir, '%s.ann' % fn_base)
        out_fn = os.path.join(out_dir, '%s-%s.examples' %
                              (fn_base, relation_type.lower()))
        out_file = io.open(out_fn, 'w', encoding='utf-8')

        brat_doc = BratDocument(ann_fn, txt_fn)
        if brat_doc.txt_content[0].isspace():
            brat_doc.txt_content = '.' + brat_doc.txt_content[1:]

        text = urllib.quote(brat_doc.txt_content)
        corenlp_doc = corenlp.annotate(text, properties=props)

        example_counter = 0
        for sentence in tqdm(corenlp_doc['sentences'], desc='Parse sentences',
                             leave=False):
            if not has_item_of_interest(sentence, brat_doc.ann_content,
                                        accept_entity_types):
                continue

            # Generate a unique example identifier
            example_id = '%s_%d_%d' % (fn_base, sentence['index'],
                                       example_counter)

            # Generate jSRE example
            example = generate_examples(example_id, sentence, brat_doc,
                                        relation_type, accept_entity_types)
            example_counter += 1

            # Save example
            out_file.write(example)

        out_file.close()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--relation_type', required=True,
                        choices=['contains', 'hasproperty'],
                        help='The valid options are contains or has_property')
    parser.add_argument('-i', '--in_dir', required=True,
                        help='Directory path to documents containing text '
                             '(.txt) and annotations (.ann)')
    parser.add_argument('-o', '--out_dir', required=True,
                        help='Directory path to the output jSRE examples')
    parser.add_argument('-c', '--corenlp_url', default='http://localhost:9000',
                        help='URL of Stanford CoreNLP server. The default is '
                             'http://localhost:9000')

    args = parser.parse_args()

    main(**vars(args))


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