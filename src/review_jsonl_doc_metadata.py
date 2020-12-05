#!/usr/bin/env python
# 
# Interactively review/edit document metadata in a .jsonl file
# and write updated content to a new file.
# Based on review_doc_metadata.py.
#
# Author: Kiri Wagstaff
# November 13, 2020
# Copyright notice at bottom of file.

import sys, os
import re
# Default readline doesn't support startup or pre-input-hooks.
# import readline
# https://stackoverflow.com/questions/28732808/python-readline-module-on-os-x-lacks-set-pre-input-hook
import gnureadline as readline
import json
import string


def main(infile, outfile):

    # check arguments
    if not os.path.exists(infile):
        print('%s file not found, exiting.' % infile)
        sys.exit(1)

    # Read in JSONL file
    with open(infile, 'r') as jf:
        docs = map(lambda x: json.loads(x), jf)
        print 'Obtained %d docs.' % len(docs)

        # Sort by filename
        docs = sorted(docs, key=lambda d: d['file'])

        for doc in docs:
            # If you want to skip to a particular abstract, use these lines.
            # TBD: make this a command-line argument.
            #(yr, abst) = map(int, doc['file'].split('/')[-1].split('.')[0].split('_'))
            #if yr < 2013 or (yr == 2013 and abst < 2219):
            #    continue
            readline.set_startup_hook()
            s = raw_input('Review %s? [Y/n/q]' % doc['file'])
            if s == 'n' or s == 'N':
                continue
            if s == 'q' or s == 'Q':
                break

            # Show the first few lines
            print('-------------------------------')
            lines = doc['content'].split('\n')
            non_empty = [l for l in lines if len(l) > 1]
            for l in non_empty[:6]:
                print(l)

            f_name = 'title'
            title = doc['metadata'].get('grobid:header_Title', '')
            if title == '':
                # If title is unknown, try to guess it from content.
                title = re.search(r'[^\.]+\.[^\.\n]+\n+([^\.]+)\.', 
                                  doc['content']).group(1).title()
            # Standardize title capitalization
            if title.isupper():
                title = string.capwords(doc['metadata'].get('grobid:header_Title', ''))
                
            readline.set_startup_hook(lambda: readline.insert_text(title.encode(sys.stdin.encoding)))
            new_value = raw_input('%s: Edit the %s: ' % (doc['file'].split('/')[-1], f_name))
            new_value = unicode(new_value, 'utf8')
            doc['metadata']['grobid:header_Title'] = new_value
            print('New title: %s' % doc['metadata']['grobid:header_Title'])

            f_name = 'authors'
            # Standardize title capitalization
            #authors = string.capwords(doc['metadata'].get('grobid:header_Authors', ''))
            authors = doc['metadata'].get('grobid:header_Authors', '')
            #if authors == '':
                # Really hard to do this automatically

            readline.set_startup_hook(lambda: readline.insert_text(authors.encode(sys.stdin.encoding)))
            new_value = raw_input('%s: Edit the %s: ' % (doc['file'].split('/')[-1], f_name))
            new_value = unicode(new_value, 'utf8')
            doc['metadata']['grobid:header_Authors'] = new_value
            print('New authors: %s' % doc['metadata']['grobid:header_Authors'])

            print('\n')

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
