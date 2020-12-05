#!/usr/bin/env python
# ingest_sqlite.py
# Mars Target Encyclopedia
# Read content from a .jsonl file (one line per source PDF) and store in sqlite DB file.
#
# Kiri Wagstaff
# August 29, 2020

import sys
import os
import json
import string
import functools
import itertools
from sqlite_mte import MteDb
from name_utils import canonical_name


# Read JSON content and return it as a generator of dictionaries (one per file)
# If 'year' is specified, it applies to all documents (e.g., for per-year .jsonl files)
# and otherwise it will be inferred for each document from the filename.
def read_json(jsonfile, ndocs, year=None, mission=''):

    with open(jsonfile) as jf:
        recs = map(lambda x: json.loads(x), jf)
        # Use yield to make this a generator and reduce memory consumption
        for rec in itertools.islice(recs, ndocs):
            yield {
                'doc_id': (str(year) + '_' + 
                           ''.join(rec['file'].split('/')[-1].split('.')[:-1]) if year is not None
                           else ''.join(rec['file'].split('/')[-1].split('.')[:-1])),
                'abstract': (int(rec['file'].split('/')[-1].split('.')[0]) if year is not None
                             else int(rec['file'].split('/')[-1].split('_')[1].split('.')[0])),
                # Capitalize first letter of each word in the title
                'title': string.capwords(rec['metadata'].\
                                         get('grobid:header_Title', '')),
                'authors': rec['metadata'].get('grobid:header_Authors', ''),
                'primary_author': '',
                'affiliations': rec['metadata'].get('grobid:header_FullAffiliations', ''),
                'venue': '',
                'year': (year if year is not None 
                         else int(rec['file'].split('/')[-1].split('_')[0])),
                'doc_url': '',
                #'content': rec['content'].strip(), # from GROBID
                'content': rec['content_ann_s'].strip(), # for annotations
                'targets': ([] if 'ner' not in rec['metadata'].keys() 
                            else [(canonical_name(r['text']), mission, r['begin'], r['end']) 
                                  for r in rec['metadata']['ner'] 
                                  if r['label'] == 'Target']),
                # Components are everything other than targets (Element, Mineral)
                'components': ([] if 'ner' not in rec['metadata'].keys() 
                               else [(canonical_name(r['text']), r['label']) for r in rec['metadata']['ner'] 
                                     if r['label'] != 'Target']),
                'contains': ([] if 'rel' not in rec['metadata'].keys()
                             else [([canonical_name(t) for t in r['target_names']], 
                                    r['target_ids'], 
                                    [canonical_name(c) for c in r['cont_names']], 
                                    r['sentence'],
                                    mission)
                                   for r in rec['metadata']['rel']])
            }


# Document feature update functions by Thamme Gowda (from insert_docs.py)
def construct_doc_url(rec):
    if rec['year'] < 2000:
        rec['doc_url'] = 'http://www.lpi.usra.edu/meetings/' + \
                         ('LPSC%s/pdf/' % (rec['year'] - 1900)) + \
                         str(rec['abstract']) + '.pdf'
    else:
        rec['doc_url'] = 'http://www.lpi.usra.edu/meetings/' + \
                         ('lpsc%s/pdf/' % rec['year']) + \
                         str(rec['abstract']) + '.pdf'
    return rec


def update_doc_venue(rec):
    rec['venue'] = 'Lunar and Planetary Science Conference, ' + \
                   ('Abstract #%d' % rec['abstract'])
    return rec


# Add the text content.  GROBID extracted this too,
# but we need it to be consistent with our annotations
# and offsets.  So we'll use our .txt instead.
def update_doc_content(rec, txtdir):
    # Works if docs are named year_abstract
    txtfile = os.path.join(txtdir, rec['doc_id'] + '.txt')
    # If not, try just getting the abstract number
    if not os.path.exists(txtfile):
        txtfile = os.path.join(txtdir, rec['doc_id'].split('_')[-1] + '.txt')

    txtf = open(txtfile, 'r')
    rec['content'] = txtf.read().decode('utf8')
    txtf.close()
    return rec


# Heuristic: first phrase in 'authors' consisting of words longer than 1 char
# and does not start with a number (affiliation)
def update_primary_author(rec):
    au = rec['authors']
    auwords = au.split()
    pa = ''
    in_last_name = False
    for auw in auwords:
        if len(auw) > 1 and auw[0].isalpha():
            if in_last_name:
                pa += (' ' + auw)
            else:
                pa = auw
                in_last_name = True
        else:
            if in_last_name:  # Done!
                break
    rec['primary_author'] = pa
    return rec


# Clean up grobid output by removing numbers (affiliations)
def update_authors(rec):
    au = rec['authors']
    auwords = au.split()
    au_cleaned = ''
    for auw in auwords:
        # Skip over numbers
        if auw.isdigit():  # handles multidigit numbers too
            continue
        # Skip over strings with commas in them (usually like "1,2")
        if ',' in auw:
            continue
        au_cleaned += (auw + ' ')
    rec['authors'] = au_cleaned
    return rec


# Update targets to include those in JSRE contains relations
def update_targets_with_JSRE(rec, mission):

    for r in rec['contains']:
        for (t, t_id) in zip(r[0], r[1]):
            (t_begin, t_end) = map(int, t_id.split('_')[1:3])
            rec['targets'] += [(canonical_name(t), mission, t_begin, t_end)]

    return rec


def main(jsonfile, dbfile, ndocs, year, mission):

    # Check arguments
    if not os.path.exists(jsonfile):
        print('Cannot find JSON file %s' % jsonfile)
        sys.exit(1)

    if ndocs == -1:
        ndocs = None  # no stopping criterion

    if year == -1:
        year = None # infer from filenames for each file

    # Read in the basic info
    recs = read_json(jsonfile, ndocs, year, mission)
    # Update individual fields
    recs = map(construct_doc_url, recs)
    recs = map(update_doc_venue, recs)
    recs = map(update_primary_author, recs)
    recs = map(update_authors, recs)
    recs = map(functools.partial(update_targets_with_JSRE, mission=mission), recs)

    # Store the records in the database
    # Use context manager so this is an atomic transaction
    with MteDb(dbfile) as db:
        db.add_records(recs)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(argument_default=argparse.SUPPRESS, 
                                     description='Read .jsonl and store in sqlite DB.')

    parser.add_argument('jsonfile', help='JSON list, one item per source PDF')
    parser.add_argument('-d', '--dbfile', 
                        default='/proj/mte/sqlite/mte_test.db',
                        help='Destination sqlite DB file')
    parser.add_argument('-n', '--ndocs',
                        type=int, default=-1,
                        help='Number of documents to ingest (default: -1 = all')
    parser.add_argument('-y', '--year',
                        type=int, default=-1,
                        help='Year for all documents (if needed to specify, e.g. for MSL)')
    parser.add_argument('-m', '--mission', default='',
                        help='Mission { mpf, phx, spi, opp, msl }')

    args = parser.parse_args()
    main(**vars(args))
