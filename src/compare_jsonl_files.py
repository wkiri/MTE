#!/usr/bin/env python
# compare_jsonl_files.py
# Compare the "rel" (relation) fields of two jsonl files. The two jsonl files
# must be generated using the exact same input documents.
# The detected differences will be written to stdout. To capture the detected
# differences in a file, please redirect stdout to a file. For example
# python compare_jsonl_files.py file1.jsonl file2.jsonl > diff.txt
#
# Steven Lu
# November 30, 2021

import os
import sys
import json
from io_utils import read_jsonlines


def convert_jsonl_to_dict(jsonl_file, accepted_relation_type):
    docs = read_jsonlines(jsonl_file)
    docs_dict = dict()

    for doc in docs:
        doc_name = doc['metadata']['resourceName']
        if type(doc_name) == list:
            doc_name = doc_name[0]
        docs_dict.setdefault(doc_name, list())

        relations = doc['metadata']['rel']
        for rel in relations:
            if rel['label'] not in accepted_relation_type:
                continue

            docs_dict[doc_name].append({
                'target_names': rel['target_names'][0],
                'target_ids': rel['target_ids'][0],
                'cont_names': rel['cont_names'][0],
                'cont_ids': rel['cont_ids'][0],
                'label': rel['label'],
                'found': False
            })

    return docs_dict


def is_same_relation(r1, r2):
    if r1['target_names'] == r2['target_names'] and \
            r1['target_ids'] == r2['target_ids'] and \
            r1['cont_names'] == r2['cont_names'] and \
            r1['cont_ids'] == r2['cont_ids'] and \
            r1['label'] == r2['label']:
        return True
    else:
        return False


def main(jsonl_file_1, jsonl_file_2, relation_type):
    for f in [jsonl_file_1, jsonl_file_2]:
        if not os.path.exists(f):
            print '[ERROR] Input file not found: %s' % os.path.abspath(f)
            sys.exit(1)

    accepted_relation_type = []
    if relation_type == 'All':
        accepted_relation_type.append('Contains')
        accepted_relation_type.append('HasProperty')
    elif relation_type == 'Contains':
        accepted_relation_type.append('Contains')
    elif relation_type == 'HasProperty':
        accepted_relation_type.append('HasProperty')
    else:
        print '[ERROR] Unrecognized relation type %s. Available options are ' \
              '"All", "Contains", or "HasProperty".' % relation_type
        sys.exit(1)

    # Extract the relations from the JSONL files
    docs_1_dict = convert_jsonl_to_dict(jsonl_file_1, accepted_relation_type)
    docs_2_dict = convert_jsonl_to_dict(jsonl_file_2, accepted_relation_type)
    if len(docs_1_dict.keys()) != len(docs_2_dict.keys()):
        print '[ERROR] The two jsonl files were not generated using the same ' \
              'input documents. The differences detected from this script ' \
              'will be inaccurate. Exit.'
        sys.exit(1)

    # Iterate through the dictionaries and find out differences
    for doc_1_name, doc_1_rels in docs_1_dict.items():
        doc_2_rels = docs_2_dict[doc_1_name]

        for r1 in doc_1_rels:
            for r2 in doc_2_rels:
                if is_same_relation(r1, r2):
                    r1['found'] = True
                    r2['found'] = True

    # Report differences
    print 'JSONL file 1: %s' % os.path.basename(jsonl_file_1)
    print 'JSONL file 2: %s' % os.path.basename(jsonl_file_2)
    print 'Relation types included for comparison: %s' % \
          json.dumps(accepted_relation_type)

    total_rels_1 = [r for rels in docs_1_dict.values() for r in rels]
    total_rels_2 = [r for rels in docs_2_dict.values() for r in rels]
    print 'Total relations found in JSONL file 1: %d' % len(total_rels_1)
    print 'Total relations found in JSONL file 2: %d' % len(total_rels_2)

    common_rels_1 = [r for rels in docs_1_dict.values() for r in rels
                     if r['found'] is True]
    common_rels_2 = [r for rels in docs_2_dict.values() for r in rels
                     if r['found'] is True]
    assert len(common_rels_1) == len(common_rels_2)
    print 'Total common relations found in both JSONL files: %d' % \
          len(common_rels_1)

    print 'Unique relations found only in JSONL file 1: %d' % \
          (len(total_rels_1) - len(common_rels_1))
    print 'Unique relations found only in JSONL file 2: %d\n' % \
          (len(total_rels_2) - len(common_rels_2))

    print 'Unique relations found only in JSONL file 1:'
    rel_ind = 0
    for doc_ind, (doc_1_name, doc_1_rels) in enumerate(docs_1_dict.items()):
        print '(%d) %s' % (doc_ind + 1, doc_1_name)

        for r in doc_1_rels:
            if r['found'] is False:
                rel_ind += 1
                print '\t%d. %s' % (rel_ind, json.dumps(r))

    print 'Unique relations found only in JSONL file 2:'
    rel_ind = 0
    for doc_ind, (doc_2_name, doc_2_rels) in enumerate(docs_2_dict.items()):
        print '(%d) %s' % (doc_ind + 1, doc_2_name)

        for r in doc_2_rels:
            if r['found'] is False:
                rel_ind += 1
                print '\t%d. %s' % (rel_ind, json.dumps(r))


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('jsonl_file_1', type=str)
    parser.add_argument('jsonl_file_2', type=str)
    parser.add_argument('--relation_type', type=str, default='All',
                        help='This argument can be used to specify the '
                             'relation type for the comparison. Available '
                             'options are All, Contains, and HasProperty. The '
                             'default is All.')

    args = parser.parse_args()
    main(**vars(args))
