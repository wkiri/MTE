#!/usr/bin/env python
# 
# Read in one .jsonl file and replace its document metadata
# (from grobid) with fields from another (hand-edited) .jsonl file.
#
# Author: Kiri Wagstaff
# April 24, 2021
# Copyright notice at bottom of file.

import sys, os
import json
import string
from review_jsonl_doc_metadata import update_field


# Using infile as the reference, read document metadata fields
# from doc file and write updated .jsonl to outfile
def main(infile, docfile, outfile):

    # check arguments
    if not os.path.exists(infile):
        print('%s file not found, exiting.' % infile)
        sys.exit(1)

    if not os.path.exists(docfile):
        print('%s file not found, exiting.' % infile)
        sys.exit(1)

    # Read in document metadata JSONL file
    with open(docfile, 'r') as jf:
        ref_docs = map(lambda x: json.loads(x), jf)
        print('Read %d docs for metadata source.' % len(ref_docs))

    # Read in source JSONL file
    with open(infile, 'r') as jf:
        docs = map(lambda x: json.loads(x), jf)
        print('Read %d docs to update.' % len(docs))

        # Sort by filename
        docs = sorted(docs, key=lambda d: d['file'])

        for doc in docs:
            # Update metadata with fields from ref_docs
            ref_doc = [r for r in ref_docs if r['file'] == doc['file']]
            if len(ref_doc) > 1:
                print('%d matches for %s' % (len(ref_doc), doc['file']))
                raw_input()

            if len(ref_doc) == 0:
                print('Could not find reference doc for %s' % doc['file'])
                # Do it by hand
                update_field(doc, 'grobid:header_Title')
                update_field(doc, 'grobid:header_Authors')
                print('\n')
            else:
                # There should be only one
                ref_doc = ref_doc[0]
                for f in ['grobid:header_Authors', 'grobid:header_Title']:
                    doc['metadata'][f] = ref_doc['metadata'].get(f, '')

        # Write out new JSONL file
        print('Writing to %s' % outfile)
        count = 0
        with open(outfile, 'wb', 1) as out:
            for doc in docs:
                out.write(json.dumps(doc))
                out.write('\n')
                count += 1
        print('Stored %d documents in %s' % (count, outfile))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(argument_default=argparse.SUPPRESS, 
                                     description='Interactively edit document metadata')

    parser.add_argument('infile', help='input JSON list filename')
    parser.add_argument('docfile', help='JSON list filename containing document metadata')
    parser.add_argument('outfile', help='where to write updated JSON list file')
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
