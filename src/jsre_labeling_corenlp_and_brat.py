#!/usr/bin/env python
#
# Read in a text file, run CoreNLP to get features (pos, lemma, NER),
# and convert it to JSRE's data ("examples") format.
#
# Authors: Kiri Wagstaff, Karanjeet Singh, Steven Lu
# Created on: September 24, 2021
# Copyright notice at bottom of file

import os
import io
import sys
import json
import urllib
import itertools
from pycorenlp import StanfordCoreNLP

# The following two lines make CoreNLP happy
reload(sys)
sys.setdefaultencoding('UTF8')


def parse(txt_file, ann_file, accept_entity_types):
    with open(txt_file) as text_file, open(ann_file) as ann_file:
        texts = text_file.read().decode('utf8')
        text_file.close()
        anns = map(lambda x: x.strip().split('\t'), ann_file)

        # FIXME: ignoring the annotations which are complex
        anns = filter(lambda x: len(x) > 2, anns)

        # FIXME: some annotations' spread have been split into many, separated
        # FIXME: by ; ignoring them
        anns = filter(lambda x: ';' not in x[1], anns)

        def __parse_ann(ann):
            spec = ann[1].split()
            entity_type = spec[0]
            ann_id = ann[0]
            markers = list(map(lambda x: int(x), spec[1:]))
            t = texts[markers[0]:markers[1]]
            if not t == ann[2]:
                print("Error: Annotation mis-match, file=%s, ann=%s, text=%s" %
                      (txt_file, str(ann), t))
                return None

            return entity_type, markers, t, ann_id

        anns = map(__parse_ann, anns)  # format
        anns = filter(lambda x: x, anns)  # skip None

        # building a tree index for easy accessing
        tree = {}
        for entity_type, pos, name, ann_id in anns:
            if entity_type in accept_entity_types:
                begin, end = pos[0], pos[1]
                if begin not in tree:
                    tree[begin] = {}
                node = tree[begin]
                if end not in node:
                    node[end] = []
                node[end].append(ann_id)

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
                if e_end in node:
                    node = {e_end: node[e_end]}  # picking one
            ann_end, labels = node.items()[0]
            if not len(labels) == 1:
                print("WARN: Duplicate ids for token: %s, id:%s. Using the "
                      "first one!" % (e['word'], str(labels)))
            label = labels[0]
            if e_end == ann_end:  # annotation ends where token ends
                continue_ann = None
            elif e_end < ann_end and label != 'O':
                continue_ann = label
                continue_ann_end = ann_end
                continue_ann_begin = e_begin
        elif continue_ann is not None and e_end <= continue_ann_end and \
                e_begin > continue_ann_begin:
            label = continue_ann  # previous label is this label
            if continue_ann_end == e_end:  # continuation ends here
                print("End")
                continue_ann = None
        else:
            continue_ann, continue_ann_end, continue_ann_begin = None, None, None
        if label != 'O':
            e['ann_id'] = label


def generate_example_id(fn_base, index, ex_id):
    # Create a unique identifier
    return '%s_%s_%s' % (fn_base, str(index), str(ex_id))


def generate_example(id, label, sentence, target_index, active_index):
    body = ''
    for t in sentence['tokens']:
        # Target entity is the agent;
        # Element entity is the target (of the relation)
        if t['index'] == target_index:
            entity_label = 'A'
        elif t['index'] == active_index:
            entity_label = 'T'
        else:
            entity_label = 'O'

        # CoreNLP indexes starting at 1
        body += '%d&&%s&&%s&&%s&&%s&&%s ' % (t['index'] - 1,
                                             t['word'],
                                             t['lemma'],
                                             t['pos'],
                                             t['ner'],
                                             entity_label)
    # Output the example
    example = '%s\t%s\t%s\n' % (label, id, body)

    return example


def parse_relation(ann_file):
    with open(ann_file, 'r') as f:
        lines = f.readlines()

        # In brat annotation, the entity type (e.g., Target, Element, Mineral)
        # is indicated with letter T and the relation type (e.g., Contains,
        # HasProperty) is indicated with letter R
        relations = [l.strip().split() for l in lines if l.startswith('R')]
        entities = [l.strip().split() for l in lines if l.startswith('T')]

    entity_dict = dict()
    for entity in entities:
        entity_dict[entity[0]] = entity[4]

    ann_relation_dict = dict()
    for rel in relations:
        ann_relation_dict[rel[0]] = {
            'relation_type': rel[1],
            'arg1': rel[2].split(':')[1],
            'arg2': rel[3].split(':')[1]
        }

    return ann_relation_dict


def has_relation(target, component, relation, ann_relation_dict):
    brat_relation_mapping = {
        'contains': 'Contains',
        'has_property': 'HasProperty'
    }
    relation_type = brat_relation_mapping[relation.lower()]

    if len(ann_relation_dict.keys()) == 0:
        return False

    for v in ann_relation_dict.values():
        if v['relation_type'] == relation_type and \
                v['arg1'].lower() == target.lower() and \
                v['arg2'].lower() == component.lower():
            return True

    return False


def build_jsre_examples(relation, in_dir, out_dir, ner_model, corenlp_url):
    if not os.path.exists(in_dir) or not os.path.isdir(in_dir):
        print '[ERROR] in_dir does not exist or is not a directory.'
        sys.exit(1)

    if not os.path.exists(ner_model) or not os.path.isfile(ner_model):
        print '[ERROR] ner_model does not exist or is not a file.'
        sys.exit(1)

    # Initialize Stanford CoreNLP server
    corenlp = StanfordCoreNLP(corenlp_url)
    props = {
        'annotators': 'tokenize,ssplit,lemma,pos,ner',
        'outputFormat': 'json',
        'ner.useSUTime': False,
        'ner.applyNumericClassifiers': False,
        'timeout': '60000',
        'ner.applyFineGrained': False,
        'ner.model': ner_model
    }

    # Create output directory
    if not os.path.exists(out_dir):
        print 'Creating output directory: %s' % os.path.abspath(out_dir)
        os.mkdir(out_dir)

    # Figure out entity types
    accept_entity_types = ['Target']
    if relation.lower() == 'contains':
        accept_entity_types.append('Element')
        accept_entity_types.append('Mineral')
    else:
        accept_entity_types.append('Property')
    print 'Accepted entity types: %s' % json.dumps(accept_entity_types)

    # Select .txt files
    in_files = [fn for fn in os.listdir(in_dir) if fn.endswith('.txt')]
    in_files.sort()
    print 'Processing %d documents.' % len(in_files)

    for fn in in_files:
        fn_base = fn[: fn.find('.txt')]
        txt_fn = '%s.txt' % fn_base
        ann_fn = '%s.ann' % fn_base
        out_fn = '%s-%s.examples' % (fn_base, relation.lower())
        ann_relation_dict = parse_relation(os.path.join(in_dir, ann_fn))

        print 'Reading in %s and %s' % (txt_fn, ann_fn)

        text, tree = parse(os.path.join(in_dir, txt_fn),
                           os.path.join(in_dir, ann_fn), accept_entity_types)

        # Reason: some tools trim/strip off the white spaces which will mismatch
        # the character offsets
        if text[0].isspace():
            text = '.' + text[1:]

        # Running CoreNLP on Document
        # Quote (with percent-encoding) reserved characters in URL for CoreNLP
        text = urllib.quote(text)
        doc = corenlp.annotate(text, properties=props)

        out_file = io.open(os.path.join(out_dir, out_fn), 'w', encoding='utf8')

        # Map brat annotations into CoreNLP sentence/token structures
        example_id = 0
        for s in doc['sentences']:
            targets = [t for t in s['tokens'] if t['ner'] == 'Target']
            active = [t for t in s['tokens']
                      if t['ner'] in accept_entity_types[1:]]

            include_brat_ann(targets, tree)
            include_brat_ann(active, tree)

            entity_pairs = itertools.product(targets, active)
            for target, component in entity_pairs:
                if 'ann_id' not in target:
                    print "No annotation exists for Target:", target['word']
                    id = generate_example_id(fn_base, s['index'], example_id)
                    example = generate_example(id, 0, s,
                                               target['index'],
                                               component['index'])
                    out_file.write(example)
                    example_id += 1
                    continue

                if 'ann_id' not in component:
                    print 'No annotation exists for %s: %s' % (relation,
                                                               component)
                    id = generate_example_id(fn_base, s['index'], example_id)
                    example = generate_example(id, 0, s,
                                               target['index'],
                                               component['index'])
                    out_file.write(example)
                    example_id += 1
                    continue

                label = 0
                if has_relation(target, component, relation, ann_relation_dict):
                    label = 1

                id = generate_example_id(fn_base, s['index'], example_id)
                example_id += 1
                example = generate_example(id, label, s,
                                           target['index'],
                                           component['index'])
                out_file.write(example)

        out_file.close()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--relation', required=True,
                        choices=['contains', 'has_property'],
                        help='The valid options are contains or has_property')
    parser.add_argument('-i', '--in_dir', required=True,
                        help='Directory path to documents containing text '
                             '(.txt) and annotations (.ann)')
    parser.add_argument('-o', '--out_dir', required=True,
                        help='Directory path to the output jSRE examples')
    parser.add_argument('-n', '--ner_model',
                        help='Path to a Named Entity Recognition (NER) model')
    parser.add_argument('-c', '--corenlp_url', default='http://localhost:9000',
                        help='URL of Stanford CoreNLP server. The default is '
                             'http://localhost:9000')

    args = parser.parse_args()

    build_jsre_examples(**vars(args))


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
