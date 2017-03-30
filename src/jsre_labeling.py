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
# Created on: March 13, 2017
# Modified on: March 30, 2017

import sys, os, io
import argparse
from pycorenlp import StanfordCoreNLP
from pysolr import Solr


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
             'ner.model': 'ner_model_train_62r15_685k14_384k15.ser.gz',
             'outputFormat': 'json'}

    # Select *.txt files
    in_files = [fn for fn in os.listdir(in_path) if fn.endswith('.txt')]
    in_files.sort()
    print 'Processing %d documents. ' % len(in_files)

    for fn in in_files:
        fnbase = fn[:fn.find('.txt')]
        in_fn = '%s.txt' % fnbase
        out_fn = '%s-%s.examples' % (fnbase, rel.lower())

        print 'Reading in %s' % in_fn
        inf = open(os.path.join(in_path, in_fn))
        text = inf.read()
        inf.close()

        # Running CoreNLP on Document
        doc = corenlp_server.annotate(text, properties=props)

        with io.open(os.path.join(out_path, out_fn), 'w', encoding='utf8') as outf:
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
                targets = [t for t in s['tokens'] if t['ner'] == 'Target']
                active = [t for t in s['tokens'] if t['ner'] == rel]

                for i in range(0, len(targets)):
                    for j in range(0, len(active)):
                        label = 0
                        qry_str = 'type:contains AND p_id:' + venue + '-' + fnbase + \
                                  ' AND target_names_tios:' + targets[i]['word'] + \
                                  ' AND cont_names_tios:' + active[j]['word']
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
                        id = '%s_%s_%s' % (fnbase,
                                           str(s['index']),
                                           str(ex_id))
                        ex_id += 1
                        body = ''
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
                            body += '%d&&%s&&%s&&%s&&%s&&%s ' % (t['index'] - 1,
                                                                 t['word'],
                                                                 t['lemma'],
                                                                 t['pos'],
                                                                 t['ner'],
                                                                 entity_label)
                        # Output the example
                        print '%s\t%s\t%s\n' % (label, id, body)
                        outf.write('%s\t%s\t%s\n' % (label, id, body))
                        print


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--relation', help='Mineral or Element', required=True)
    parser.add_argument('-v', '--venue', help='Example: lpsc15', required=True)
    parser.add_argument('-i', '--input', help='Directory path to documents containing content', required=True)
    parser.add_argument('-o', '--output', help='Directory path where jSRE examples to be placed', required=True)
    parser.add_argument('-s', '--solr_url', help='URL of Solr Server; Default: http://localhost:8983/solr/docs',
                        default='http://localhost:8983/solr/docs')
    parser.add_argument('-n', '--corenlp_url', help='URL of Stanford CoreNlp server; Default: http://localhost:9000',
                        default='http://localhost:9000')
    args = parser.parse_args()
    build_jsre_examples(args.relation, args.venue, args.input, args.output, args.solr_url, args.corenlp_url)
