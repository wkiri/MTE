#!/usr/bin/env python
# sqlite.py
# Mars Target Encyclopedia
# Read in sqlite database file, and then export the tables to CSV files.
#
# Steven Lu
# November 12, 2020

import os
import re
import sys
import sqlite3
import pandas as pd


def main(db_file, out_dir, fix_double_quotes):
    if not os.path.exists(db_file):
        print '[ERROR] Database file not found: %s' % os.path.abspath(db_file)
        sys.exit(1)

    if not os.path.exists(out_dir):
        os.mkdir(out_dir)
        print '[INFO] Created output directory: %s' % os.path.abspath(out_dir)

    connection = sqlite3.connect(db_file)

    # Export the `targets` table into targets.csv.
    targets_csv = os.path.join(out_dir, 'targets.csv')
    targets_df = pd.read_sql_query('SELECT * FROM targets '
                                   'ORDER BY target_id ASC', connection)
    if fix_double_quotes:
        targets_df.replace(regex='"', value="''", inplace=True)
        print '[INFO] internal double quotes were replaced with single ' \
              'quotes for targets.csv'
    targets_df.to_csv(targets_csv, index=False, encoding='utf-8',
                      line_terminator='\r\n')
    print '[INFO] targets table exported to %s' % targets_csv

    # Export the `components` and `properties` tables CSV files
    # with "orphaned" components (those that do not appear in ref_table) removed.
    for (field, table, ref_table) in \
        [('component_name', 'components', 'contains'),
         ('property_name', 'properties', 'has_property')]:
        csv_file = os.path.join(out_dir, '%s.csv' % table)
        df = pd.read_sql_query('SELECT * FROM %s '
                               'WHERE %s IN '
                               '(SELECT %s FROM %s);' %
                               (table, field, field, ref_table),
                               connection)
        if fix_double_quotes:
            df.replace(regex='"', value="''", inplace=True)
            print('[INFO] internal double quotes were replaced with single '
                  'quotes for %s' % csv_file)
        df.to_csv(csv_file, index=False, encoding='utf-8',
                  line_terminator='\r\n')
        print('[INFO] %s table exported to %s' % (table, csv_file))

    # Export the `sentences` table into sentences.csv.
    sentences_csv = os.path.join(out_dir, 'sentences.csv')
    sentences_df = pd.read_sql_query('SELECT * FROM sentences', connection)
    if fix_double_quotes:
        sentences_df.replace(regex='"', value="''", inplace=True)
        print '[INFO] internal double quotes were replaced with single ' \
              'quotes for sentences.csv'
    sentences_df.to_csv(sentences_csv, index=False, encoding='utf-8',
                        line_terminator='\r\n')
    print '[INFO] sentences table exported to %s' % sentences_csv

    # Export the `documents` table into documents.csv with content and reviewer
    # fields excluded.
    documents_csv = os.path.join(out_dir, 'documents.csv')
    documents_df = pd.read_sql_query('SELECT doc_id, abstract, title, authors, '
                                     'primary_author, year, venue, doc_url '
                                     'FROM documents WHERE doc_id in '
                                     '(SELECT doc_id from sentences)',
                                     connection)
    if fix_double_quotes:
        documents_df.replace(regex='"', value="''", inplace=True)
        print '[INFO] internal double quotes were replaced with single ' \
              'quotes for documents.csv'
    documents_df.to_csv(documents_csv, index=False, encoding='utf-8',
                        line_terminator='\r\n')
    print '[INFO] documents table exported to %s' % documents_csv

    # Export the `mentions` table into mentions.csv.
    mentions_csv = os.path.join(out_dir, 'mentions.csv')
    mentions_df = pd.read_sql_query('SELECT * FROM mentions '
                                    'ORDER BY target_id ASC', connection)
    if fix_double_quotes:
        mentions_df.replace(regex='"', value="''", inplace=True)
        print '[INFO] internal double quotes were replaced with single ' \
              'quotes for mentions.csv'
    mentions_df.to_csv(mentions_csv, index=False, encoding='utf-8',
                       line_terminator='\r\n')
    print '[INFO] mentions table exported to %s' % mentions_csv

    # Export the `contains` table into contains.csv.
    contains_csv = os.path.join(out_dir, 'contains.csv')
    contains_df = pd.read_sql_query('SELECT * FROM contains', connection)
    if fix_double_quotes:
        contains_df.replace(regex='"', value="''", inplace=True)
        print '[INFO] internal double quotes were replaced with single ' \
              'quotes for contains.csv'
    contains_df.to_csv(contains_csv, index=False, encoding='utf-8',
                       line_terminator='\r\n')
    print '[INFO] contains table exported to %s' % contains_csv

    # Export the `has_property` table into has_property.csv.
    has_property_csv = os.path.join(out_dir, 'has_property.csv')
    has_property_df = pd.read_sql_query('SELECT * FROM has_property',
                                        connection)
    if fix_double_quotes:
        has_property_df.replace(regex='"', value="''", inplace=True)
        print '[INFO] internal double quotes were replaced with single ' \
              'quotes for has_property.csv'
    has_property_df.to_csv(has_property_csv, index=False, encoding='utf-8',
                           line_terminator='\r\n')
    print '[INFO] has_property table exported to %s' % has_property_csv

    # Export the `aliases` table into aliases.csv.
    aliases_csv = os.path.join(out_dir, 'aliases.csv')
    aliases_df = pd.read_sql_query('SELECT * FROM aliases', connection)
    if fix_double_quotes:
        aliases_df.replace(regex='"', value="''", inplace=True)
        print '[INFO] internal double quotes were replaced with single ' \
              'quotes for aliases.csv'
    aliases_df.to_csv(aliases_csv, index=False, encoding='utf-8',
                      line_terminator='\r\n')
    print '[INFO] aliases table exported to %s' % aliases_csv

    connection.close()
    print '[INFO] All done.'


# This function will replace the embedded double quotes with (by default) two
# single quotes in a csv file. For example, the following record
#
# 1998_1338,1998_1338-0,"It was suggested that these drifts, ""Roadrunner""
# and ""Jenkins,"" might be composed of ""light""-colored grains
#
# by default will be converted to
#
# 1998_1338,1998_1338-0,"It was suggested that these drifts, ''Roadrunner''
# and ''Jenkins,'' might be composed of ''light''-colored grains
def replace_internal_double_quote(csv_file, replace_with="''"):
    pattern = r'""([^"]+)""'
    with open(csv_file, 'r') as f:
        csv_lines = f.readlines()

    out_f = open(csv_file, 'w')
    for line in csv_lines:
        matches = [x.group() for x in re.finditer(pattern, line)]

        for m in matches:
            s = replace_with + m[2:]
            s = s[:-2] + replace_with
            line = line.replace(m, s)

        out_f.write(line)

    out_f.close()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Read in sqlite database file,'
                                                 ' and then export the tables '
                                                 'to CSV files')
    parser.add_argument('db_file', type=str, help='Path to sqlite DB file')
    parser.add_argument('out_dir', type=str, default='./',
                        help='Path to the output directory that contains the '
                             'exported CSV files. Default is current dir.')
    parser.add_argument('--fix_double_quotes', action='store_true',
                        help='Optional post-processing step to replace an '
                             'embedded double-quote with two single-quotes. '
                             'Default is False (disabled).')

    args = parser.parse_args()
    main(**vars(args))
