#!/usr/bin/env python
# sqlite.py
# Mars Target Encyclopedia
# Read in sqlite database file, and then export the tables to CSV files.
#
# Steven Lu
# November 12, 2020

import os
import sys
import sqlite3
import pandas as pd


def main(db_file, out_dir):
    if not os.path.exists(db_file):
        print '[ERROR] Database file not found: %s' % os.path.abspath(db_file)
        sys.exit(1)

    if not os.path.exists(out_dir):
        os.mkdir(out_dir)
        print '[INFO] Created output directory: %s' % os.path.abspath(out_dir)

    connection = sqlite3.connect(db_file)

    # Export the `targets` table into targets.csv with "orphaned" targets
    # removed.
    targets_csv = os.path.join(out_dir, 'targets.csv')
    targets_df = pd.read_sql_query('SELECT * FROM targets WHERE target_id IN '
                                   '(SELECT target_id FROM mentions);',
                                   connection)
    targets_df.to_csv(targets_csv, index=False, encoding='utf-8')
    print '[INFO] targets table exported to %s' % targets_csv

    # Export the `components` table into components.csv with "orphaned"
    # components removed.
    components_csv = os.path.join(out_dir, 'components.csv')
    components_df = pd.read_sql_query('SELECT * FROM components '
                                      'WHERE component_name IN '
                                      '(SELECT component_name FROM contains);',
                                      connection)
    components_df.to_csv(components_csv, index=False, encoding='utf-8')
    print '[INFO] components table exported to %s' % components_csv

    # Export the `sentences` table into sentences.csv.
    sentences_csv = os.path.join(out_dir, 'sentences.csv')
    sentences_df = pd.read_sql_query('SELECT * FROM sentences', connection)
    sentences_df.to_csv(sentences_csv, index=False, encoding='utf-8')
    print '[INFO] sentences table exported to %s' % sentences_csv

    # Export the `documents` table into documents.csv with content and reviewer
    # fields excluded.
    documents_csv = os.path.join(out_dir, 'documents.csv')
    documents_df = pd.read_sql_query('SELECT doc_id, abstract, title, authors, '
                                     'primary_author, year, venue, doc_url '
                                     'FROM documents WHERE doc_id in '
                                     '(SELECT doc_id from sentences)',
                                     connection)
    documents_df.to_csv(documents_csv, index=False, encoding='utf-8')
    print '[INFO] documents table exported to %s' % documents_csv

    # Export the `mentions` table into mentions.csv.
    mentions_csv = os.path.join(out_dir, 'mentions.csv')
    mentions_df = pd.read_sql_query('SELECT * FROM mentions', connection)
    mentions_df.to_csv(mentions_csv, index=False, encoding='utf-8')
    print '[INFO] mentions table exported to %s' % mentions_csv

    # Export the `contains` table into contains.csv.
    contains_csv = os.path.join(out_dir, 'contains.csv')
    contains_df = pd.read_sql_query('SELECT * FROM contains', connection)
    contains_df.to_csv(contains_csv, index=False, encoding='utf-8')
    print '[INFO] contains table exported to %s' % contains_csv

    connection.close()
    print '[INFO] All done.'


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Read in sqlite database file,'
                                                 ' and then export the tables '
                                                 'to CSV files')
    parser.add_argument('db_file', type=str, help='Path to sqlite DB file')
    parser.add_argument('out_dir', type=str, default='./',
                        help='Path to the output directory that contains the '
                             'exported CSV files. Default is current dir.')

    args = parser.parse_args()
    main(**vars(args))
