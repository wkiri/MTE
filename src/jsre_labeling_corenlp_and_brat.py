#!/usr/bin/env python
#
# Read in a text file, run CoreNLP to get features (pos, lemma, NER),
# and convert it to JSRE's data ("examples") format.
#
# Authors: Kiri Wagstaff and Karanjeet Singh
# Created on: March 13, 2017
#
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

import sys, os, io
import argparse
from pycorenlp import StanfordCoreNLP
from pysolr import Solr


def parse(txt_file, ann_file, accept_entities):
    with open(txt_file) as text_file, open(ann_file) as ann_file:
        texts = text_file.read().decode('utf8')
        text_file.close()
        anns = map(lambda x: x.strip().split('\t'), ann_file)
        anns = filter(lambda x: len(x) > 2, anns)
        # FIXME: ignoring the annotations which are complex

        anns = filter(lambda x: ';' not in x[1], anns)

        # FIXME: some annotations' spread have been split into many, separated by ; ignoring them

        def __parse_ann(ann):
            spec = ann[1].split()
            entity_type = spec[0]
            ann_id = ann[0]
            markers = list(map(lambda x: int(x), spec[1:]))
            # t = ' '.join([texts[begin:end] for begin,end in zip(markers[::2], markers[1::2])])
            t = texts[markers[0]:markers[1]]
            if not t == ann[2]:
                print("Error: Annotation mis-match, file=%s, ann=%s" % (txt_file, str(ann)))
                return None
            return (entity_type, markers, t, ann_id)

        anns = map(__parse_ann, anns)  # format
        anns = filter(lambda x: x, anns)  # skip None

        # building a tree index for easy accessing
        tree = {}
        for entity_type, pos, name, ann_id in anns:
            if entity_type in accept_entities:
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
                #print("WARN: multiple starts at ", e_begin, node)
                if e_end in node:
                    #e['ann_id'] = node[e_end][0]  # picking one
                    node = {e_end: node[e_end]}  # picking one
                    #print("Chose:", node)
            ann_end, labels = node.items()[0]
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
                print("End")
                continue_ann = None
        else:
            continue_ann, continue_ann_end, continue_ann_begin = None, None, None
        if label != 'O':
            e['ann_id'] = label


def generate_example_id(fnbase, index, ex_id):
    # Create a unique identifier
    return '%s_%s_%s' % (fnbase, str(index), str(ex_id))


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
    print example
    return example


def build_jsre_examples(rel, venue, in_path, out_path, solr_url, corenlp_url):
    """
    Build jSRE examples from CoreNLP NER and Brat Annotations
    :param rel: relation to extract
    :param venue: example: lpsc15
    :param in_path: path to the input directory
    :param out_path: path to the output directory
    :param solr_url: URL of Solr Server
    :param corenlp_url: URL of Stanford CoreNLP Server
    :return:
    """
    # Configuration
    corenlp_server = StanfordCoreNLP(corenlp_url)
    solr_server = Solr(solr_url)
    props = {'annotators': 'tokenize,ssplit,lemma,pos,ner',
             #'ner.model': 'ner_model_train_62r15_685k14_384k15.ser.gz',
             'ner.model': 'ner_model_train_63r15v2_685k14-no-ref_384k15-no-ref.ser.gz',
             'outputFormat': 'json'}

    if not os.path.exists(out_path):
        print 'Creating output directory %s' % out_path
        os.mkdir(out_path)

    # Select *.txt files
    in_files = [fn for fn in os.listdir(in_path) if fn.endswith('.txt')]
    in_files.sort()
    print 'Processing %d documents. ' % len(in_files)

    for fn in in_files:
        fnbase = fn[:fn.find('.txt')]
        in_fn = '%s.txt' % fnbase
        ann_fn = '%s.ann' % fnbase
        out_fn = '%s-%s.examples' % (fnbase, rel.lower())

        print 'Reading in %s and %s' % (in_fn, ann_fn)
        #for line in convert(corenlp_server, os.path.join(in_path, in_fn), os.path.join(in_path, ann_fn)):
        #    print line
        accept_entities = {'Target', rel}
        text, tree = parse(os.path.join(in_path, in_fn), os.path.join(in_path, ann_fn), accept_entities)

        if text[0].isspace():
            text = '.' + text[1:]
            # Reason: some tools trim/strip off the white spaces
            #  which will mismatch the character offsets

        # Running CoreNLP on Document
        doc = corenlp_server.annotate(text, properties=props)

        with io.open(os.path.join(out_path, out_fn), 'w', encoding='utf8') as outf:
            # Map Raymond's .ann (brat) annotations into the CoreNLP-parsed
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
                targets = [t for t in s['tokens'] if t['ner'] == 'Target']
                active = [t for t in s['tokens'] if t['ner'] == rel]

                include_brat_ann(targets, tree)
                include_brat_ann(active, tree)

                for i in range(0, len(targets)):
                    for j in range(0, len(active)):
                        if 'ann_id' not in targets[i]:
                            print "No annotation exist for Target:", targets[i]['word']
                            id = generate_example_id(fnbase, s['index'], ex_id)
                            example = generate_example(id, 0, s, targets[i]['index'], active[j]['index'])
                            outf.write(example)
                            ex_id += 1
                            continue
                        if 'ann_id' not in active[j]:
                            print 'No annotation exist for %s: %s' % (rel, active[j]['word'])
                            id = generate_example_id(fnbase, s['index'], ex_id)
                            example = generate_example(id, 0, s, targets[i]['index'], active[j]['index'])
                            outf.write(example)
                            ex_id += 1
                            continue
                        label = 0
                        qry_str = 'type:contains AND p_id:' + venue + '-' + fnbase + \
                                  ' AND targets_ss:' + targets[i]['ann_id'] + \
                                  ' AND cont_ss:' + active[j]['ann_id']
                        print qry_str, "\n\n"
                        resp = solr_server.search(qry_str, None, fl='id')
                        if resp and resp.hits > 0:
                            label = 1

                        # Change label from 1 to 2 if needed
                        if label != 0:
                            if targets[i]['index'] < active[j]['index']:
                                label = 1
                            else:
                                label = 2

                        # Create a unique identifier
                        id = generate_example_id(fnbase, s['index'], ex_id)
                        ex_id += 1
                        example = generate_example(id, label, s, targets[i]['index'], active[j]['index'])
                        outf.write(example)
                        print


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--relation', help='Mineral or Element', required=True)
    parser.add_argument('-v', '--venue', help='Example: lpsc15', required=True)
    parser.add_argument('-i', '--input', help='Directory path to documents containing text and annotations', required=True)
    parser.add_argument('-o', '--output', help='Directory path where jSRE examples to be placed', required=True)
    parser.add_argument('-s', '--solr_url', help='URL of Solr Server; Default: http://localhost:8983/solr/docs',
                        default='http://localhost:8983/solr/docs')
    parser.add_argument('-n', '--corenlp_url', help='URL of Stanford CoreNlp server; Default: http://localhost:9000',
                        default='http://localhost:9000')
    args = parser.parse_args()
    build_jsre_examples(args.relation, args.venue, args.input, args.output, args.solr_url, args.corenlp_url)
