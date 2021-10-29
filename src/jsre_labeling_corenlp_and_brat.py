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
import re
import sys
import copy
import urllib
import itertools
from pycorenlp import StanfordCoreNLP
from brat_annotation_sqlite import BratDocument
from brat_annotation_sqlite import TYPE_ENTITY
from brat_annotation_sqlite import TYPE_RELATION
from brat_annotation_sqlite import TYPE_EVENT


# Stanford CoreNLP will split most of the hyphenated words by default with
# exceptions in Supplementary Guidelines for ETTB 2.0.
# https://www.ldc.upenn.edu/sites/www.ldc.upenn.edu/files/etb-supplementary-guidelines-2009-addendum.pdf
# The exceptions are defined in section 1.2 Hyphenated Words.
# In order to match the tokens between CoreNLP and the Brat annotations, we
# need to tokenize the Brat annotations the same way as CoreNLP. If the
# affixes in the following list are inside a Brat annotation, we will not
# split this Brat annotation.
ETTB_AFFIXES = ['e-', 'a-', 'u-', 'x-', 'agro-', 'ante-', 'anti-', 'arch-',
                'be-', 'bio-', 'co-', 'counter-', 'cross-', 'cyber-', 'de-',
                'eco-', '-esque', '-ette', 'ex-', 'extra-', '-fest', '-fold',
                '-gate', 'inter-', 'intra-', '-itis', '-less', 'macro-',
                'mega-', 'micro-', 'mid-', 'mini-', 'mm-hm', 'mm-mm', '-most',
                'multi-', 'neo-', 'non-', 'o-kay', '-o-torium', 'over-', 'pan-',
                'para-', 'peri-', 'post-', 'pre-', 'pro-', 'pseudo-', 'quasi-',
                '-rama', 're-', 'semi-', 'sub-', 'super-', 'tri-', 'uh-huh',
                'uh-oh', 'ultra-', 'un-', 'uni-', 'vice-', '-wise']


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


def generate_examples(sentence, relevant_ann, fn_base, out_file):
    example_counter = 0

    # Step 1: Generate all positive relation examples within the sentence. Note
    # that there could be more than one positive relations in one sentence.
    example_counter = generate_positive_examples(sentence, relevant_ann,
                                                 example_counter, fn_base,
                                                 out_file)

    # Step 2: Generate all negative relation examples within the sentence. Note
    # that there could be more than one negative relations in one sentence.
    generate_negative_examples(sentence, relevant_ann, example_counter, fn_base,
                               out_file)


def get_ann_by_id(entity_ann_list, ann_id):
    ret_entity_ann = None
    for entity_ann in entity_ann_list:
        if entity_ann.ann_id == ann_id:
            ret_entity_ann = entity_ann

    return ret_entity_ann


def remove_ann_by_id(ann_list, ann_id):
    for entity_ann in ann_list:
        if entity_ann.ann_id == ann_id:
            ann_list.remove(entity_ann)
            break


def remove_nested_ann(entity_ann_list, relation_ann_list):
    target_entity_list = [ann for ann in entity_ann_list if ann.label == 'Target']
    active_entity_list = [ann for ann in entity_ann_list if ann.label != 'Target']
    entity_pairs = itertools.product(target_entity_list, active_entity_list)

    for target_entity, active_entity in entity_pairs:
        if active_entity.name in target_entity.name and \
                active_entity.start >= target_entity.start and \
                active_entity.end <= target_entity.end:
            entity_ann_list.remove(active_entity)

            for relation_ann in list(relation_ann_list):
                if (relation_ann.type == TYPE_RELATION and
                        relation_ann.arg2 == active_entity.ann_id) or \
                        (relation_ann.type == TYPE_EVENT and
                        active_entity.ann_id in relation_ann.conts):
                    relation_ann_list.remove(relation_ann)


def get_entity_type_and_label(token, target_entity, active_entity,
                              entity_ann_list):
    entity_ann_list_copy = copy.deepcopy(entity_ann_list)
    jsre_entity_type = 'O'
    jsre_entity_label = 'O'

    offset_begin = token['characterOffsetBegin']
    offset_end = token['characterOffsetEnd']
    word = token['originalText']

    if offset_begin >= target_entity.start and \
            offset_end <= target_entity.end and \
            word.lower() in target_entity.name.lower():
        jsre_entity_type = target_entity.label
        jsre_entity_label = 'A'  # 'A' means jSRE agent
    elif offset_begin >= active_entity.start and \
            offset_end <= active_entity.end and \
            word.lower() in active_entity.name.lower():
        jsre_entity_type = active_entity.label
        jsre_entity_label = 'T'  # 'T' means jSRE target
    else:
        remove_ann_by_id(entity_ann_list_copy, target_entity.ann_id)
        remove_ann_by_id(entity_ann_list_copy, active_entity.ann_id)

        for entity in entity_ann_list_copy:
            if offset_begin >= entity.start \
                    and offset_end <= entity.end and \
                    word.lower() in entity.name.lower():
                jsre_entity_type = entity.label

    return jsre_entity_type, jsre_entity_label


def get_sub_entity(target_entity):
    split_flag = True
    for affix in ETTB_AFFIXES:
        if affix in target_entity.name.lower():
            split_flag = False
            break

    # Split the target entity by space, hyphen, and underscore.
    if split_flag:
        entity_tokens = re.split(' |-|_', target_entity.name)
    else:
        entity_tokens = [target_entity.name]

    if len(entity_tokens) == 0:
        return target_entity

    target_start = target_entity.start

    sub_target_entity_list = list()
    for idx, entity_token in enumerate(entity_tokens):
        # Create an empty object-like function
        sub_entity = lambda: None
        sub_entity.ann_id = '%s_%d' % (target_entity.ann_id, idx)
        sub_entity.name = entity_token
        sub_entity.type = target_entity.type
        sub_entity.label = target_entity.label
        sub_entity.start = target_start + target_entity.name.index(entity_token)
        sub_entity.end = sub_entity.start + len(entity_token)

        sub_target_entity_list.append(sub_entity)

    return sub_target_entity_list


def convert_event_to_relation(event_ann_list):
    convert_relation_ann_list = list()
    for event_ann in event_ann_list:
        relation_pairs = itertools.product(event_ann.targs, event_ann.conts)
        for ind, (target_id, component_id) in enumerate(relation_pairs):
            # Create an empty object-like function
            relation_ann = lambda: None
            relation_ann.ann_id = '%s_%d' % (event_ann.ann_id, ind)
            relation_ann.type = TYPE_RELATION
            relation_ann.label = event_ann.label
            relation_ann.arg1 = target_id
            relation_ann.arg2 = component_id

            convert_relation_ann_list.append(relation_ann)

    return convert_relation_ann_list


def generate_positive_examples(sentence, relevant_ann_list, example_counter,
                               fn_base, out_file):
    relation_ann_list = [ann for ann in relevant_ann_list
                         if ann.type == TYPE_RELATION]
    entity_ann_list = [ann for ann in relevant_ann_list
                       if ann.type == TYPE_ENTITY]
    event_ann_list = [ann for ann in relevant_ann_list
                      if ann.type == TYPE_EVENT]
    converted_relation_ann_list = convert_event_to_relation(event_ann_list)
    relation_ann_list.extend(converted_relation_ann_list)

    if len(relation_ann_list) == 0:
        return example_counter

    sentence_start = sentence['tokens'][0]['characterOffsetBegin']
    sentence_end = sentence['tokens'][-1]['characterOffsetEnd']

    for relation_ann in relation_ann_list:
        target_entity = get_ann_by_id(entity_ann_list, relation_ann.arg1)
        active_entity = get_ann_by_id(entity_ann_list, relation_ann.arg2)

        if target_entity is None or active_entity is None:
            continue

        # If target and active entities are in the same sentence, generate a
        # positive jsre example for the entity pair
        if target_entity.start >= sentence_start and \
                target_entity.end <= sentence_end and \
                active_entity.start >= sentence_start and \
                active_entity.end <= sentence_end:
            # An entity could have multiple words (e.g., Scooby Doo).
            # We need to split multi-words entity into multiple
            # single-word entities. For example, the multi-words target
            # entity Scooby Doo will be split into two single-word entities
            # Scooby and Doo.
            sub_target_entity_list = get_sub_entity(target_entity)
            sub_active_entity_list = get_sub_entity(active_entity)
            sub_entity_pairs = itertools.product(sub_target_entity_list,
                                                 sub_active_entity_list)
            for sub_target_entity, sub_active_entity in sub_entity_pairs:
                example_body = ''

                for token in sentence['tokens']:
                    entity_type, entity_label = get_entity_type_and_label(token,
                        sub_target_entity, sub_active_entity, entity_ann_list)

                    example_body += '%d&&%s&&%s&&%s&&%s&&%s ' % (
                        token['index'] - 1, token['word'], token['lemma'],
                        token['pos'], entity_type, entity_label)

                # This is to handle the case where an example body doesn't
                # contain jSRE Agent or jSRE Target.
                if '&&A ' not in example_body or '&&T ' not in example_body:
                    print 'Example created for entity %s %s and entity %s %s ' \
                          'are skipped because we cannot match the CoreNLP ' \
                          'tokens to Brat annotations' % \
                          (sub_target_entity.ann_id, sub_target_entity.name,
                           sub_active_entity.ann_id, sub_active_entity.name)
                    continue

                example_id = '%s_%d_%d' % (fn_base, sentence['index'],
                                           example_counter)
                example_counter += 1
                # '1' means jSRE positive example
                example = '%s\t%s\t%s\n' % ('1', example_id, example_body)
                out_file.write(example)

    return example_counter


def generate_negative_examples(sentence, relevant_ann_list, example_counter,
                               fn_base, out_file):
    sentence_start = sentence['tokens'][0]['characterOffsetBegin']
    sentence_end = sentence['tokens'][-1]['characterOffsetEnd']

    relation_ann_list = [ann for ann in relevant_ann_list
                         if ann.type == TYPE_RELATION]
    event_ann_list = [ann for ann in relevant_ann_list
                      if ann.type == TYPE_EVENT]
    converted_relation_ann_list = convert_event_to_relation(event_ann_list)
    relation_ann_list.extend(converted_relation_ann_list)
    entity_ann_list = [ann for ann in relevant_ann_list
                       if ann.type == TYPE_ENTITY and
                       ann.start >= sentence_start and
                       ann.end <= sentence_end]
    target_ann_list = [ann for ann in entity_ann_list if ann.label == 'Target']
    active_ann_list = [ann for ann in entity_ann_list if ann.label != 'Target']

    if len(target_ann_list) == 0 or len(active_ann_list) == 0:
        return

    entity_pairs = itertools.product(target_ann_list, active_ann_list)
    for target_entity, active_entity in entity_pairs:
        skip_flag = False
        for relation_ann in relation_ann_list:
            if target_entity.ann_id == relation_ann.arg1 and \
                    active_entity.ann_id == relation_ann.arg2:
                # This is the pair to generate positive example or being skipped
                # by the function that generates positive examples if the
                # entities are not in the same sentence. Here, we skip it
                # because we are generating negative examples.
                skip_flag = True
                break

        if skip_flag:
            continue

        # An entity could have multiple words (e.g., Scooby Doo).
        # We need to split multi-words entity into multiple
        # single-word entities. For example, the multi-words target
        # entity Scooby Doo will be split into two single-word entities
        # Scooby and Doo.
        sub_target_entity_list = get_sub_entity(target_entity)
        sub_active_entity_list = get_sub_entity(active_entity)
        sub_entity_pairs = itertools.product(sub_target_entity_list,
                                             sub_active_entity_list)
        for sub_target_entity, sub_active_entity in sub_entity_pairs:
            example_body = ''

            for token in sentence['tokens']:
                entity_type, entity_label = get_entity_type_and_label(token,
                    sub_target_entity, sub_active_entity, entity_ann_list)

                example_body += '%d&&%s&&%s&&%s&&%s&&%s ' % (token['index'] - 1,
                                                             token['word'],
                                                             token['lemma'],
                                                             token['pos'],
                                                             entity_type,
                                                             entity_label)

            # This is to handle the case where an example body doesn't
            # contain jSRE Agent or jSRE Target.
            if '&&A ' not in example_body or '&&T ' not in example_body:
                print 'Warn: example created for entity [%s %s] and entity [%s ' \
                      '%s] are skipped because we cannot match the CoreNLP ' \
                      'tokens to Brat annotations' % \
                      (sub_target_entity.ann_id, sub_target_entity.name,
                       sub_active_entity.ann_id, sub_active_entity.name)
                continue

            example_id = '%s_%d_%d' % (fn_base, sentence['index'],
                                       example_counter)
            example_counter += 1
            # '0' means jSRE negative example
            example = '%s\t%s\t%s\n' % ('0', example_id, example_body)
            out_file.write(example)


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
    accept_entity_types = list()
    if relation_type.lower() == 'contains':
        accept_entity_types.append('Element')
        accept_entity_types.append('Mineral')
    else:
        accept_entity_types.append('Property')

    # Get a list of all text documents
    in_files = [fn for fn in os.listdir(in_dir) if fn.endswith('.txt')]
    in_files.sort()
    n_files = len(in_files)
    print 'Number of documents to process: %d' % n_files

    for ind, fn in enumerate(in_files):
        fn_base = fn[: fn.find('.txt')]
        print '(%d/%d) Processing %s' % (ind + 1, n_files, fn_base)

        txt_fn = os.path.join(in_dir, '%s.txt' % fn_base)
        ann_fn = os.path.join(in_dir, '%s.ann' % fn_base)
        out_fn = os.path.join(out_dir, '%s-%s.examples' %
                              (fn_base, relation_type.lower()))
        out_file = io.open(out_fn, 'w', encoding='utf-8')

        brat_doc = BratDocument(ann_fn, txt_fn, canonical_mapping=False)
        if brat_doc.txt_content[0].isspace():
            brat_doc.txt_content = '.' + brat_doc.txt_content[1:]

        text = urllib.quote(brat_doc.txt_content)
        corenlp_doc = corenlp.annotate(text, properties=props)

        # Get active entities and relations
        all_entity_types = accept_entity_types + ['Target']
        entity_ann_list = [ann for ann in brat_doc.ann_content
                           if ann.label in all_entity_types]
        relation_ann_list = [ann for ann in brat_doc.ann_content
                             if ann.label.lower() == relation_type and
                             (ann.type == TYPE_RELATION or
                              ann.type == TYPE_EVENT)]
        remove_nested_ann(entity_ann_list, relation_ann_list)
        relevant_ann_list = entity_ann_list + relation_ann_list

        if len(relevant_ann_list) == 0:
            # If a .ann file doesn't contain any relevant annotations, skip it.
            continue

        for sentence in corenlp_doc['sentences']:
            generate_examples(sentence, relevant_ann_list, fn_base, out_file)

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
