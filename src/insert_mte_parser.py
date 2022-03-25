#!/usr/bin/env python
# insert_mte_parser.py
# Mars Target Encyclopedia
# Insert `mte_parser` field to each record in a jsonl file that contains only
# LPSC documents.
# Note that this script is developed as a quick workaround to insert
# `mte_parser` field to an existing jsonl file. Use with caution.
#
# Steven Lu
# March 25, 2022

import os
import sys
import json
import itertools


def main(in_lpsc_jsonl_file, out_jsonl_file):
    if not os.path.exists(in_lpsc_jsonl_file):
        print '[ERROR] Input JSONL file does not exist.'
        sys.exit(1)

    out_jsonl = open(out_jsonl_file, 'wb', 1)

    with open(in_lpsc_jsonl_file) as f:
        recs = map(lambda x: json.loads(x), f)

        for rec in itertools.islice(recs, None):
            rec['metadata']['mte_parser'] = ['TikaParser', 'AdsParser',
                                             'LpscParser', 'JsreParser']
            out_jsonl.write(json.dumps(rec))
            out_jsonl.write('\n')

    out_jsonl.close()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('in_lpsc_jsonl_file', type=str)
    parser.add_argument('out_jsonl_file', type=str)

    args = parser.parse_args()
    main(**vars(args))
