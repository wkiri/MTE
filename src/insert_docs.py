#!/usr/bin/env python
'''
This script inserts document content to PSQL table.

1. To create table run `create_db.py` which should be sitting beside this script in the same directory
2. To obtain the input JSON documents for insertion, visit https://github.com/USCDataScience/parser-indexer-py
'''
#__author__ = 'Thamme Gowda'
#__version__ = '0.1'
# Copyright notice at bottom of file.

import psycopg2
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import os
import json
import string
from dbutils import insert_into_table
import sys
reload(sys)
sys.setdefaultencoding('UTF8') # making UTF8 as default encoding

class PSQLDb(object):
    '''
    An object this class represents connection to PSQL Database.
    '''
    def __init__(self, dbname, userid):
        '''
        @param dbname  : name of the database to connect to
        @param userid  : user id to use to establish connection
        '''
        self.dbname = dbname
        self.userid = userid

    def __enter__(self):
        conn_spec = "dbname=%s user=%s" % (self.dbname, self.userid)
        print('connecting :: %s' % conn_spec)
        self.db = psycopg2.connect(conn_spec)
        print("DB Connection Encoding = %s"%self.db.encoding)
        return self

    def insert_all(self, table_name, records):
        '''
        inserts all the records in the iterator to table
        @param table_name : name of the table to insert
        @param records : iterator of documents
        '''
        with self.db.cursor() as cursor:
            count = 0
            for rec in records:
                count += 1
                insert_into_table(cursor=cursor, table=table_name,
                                columns=rec.keys(), values=rec.values())
            return count

    def __exit__(self, exc_type, exc_value, traceback):
        print("Disconnecting :: %s" % self.dbname)
        self.db.commit()
        self.db.close()


def get_records(f_name):
    '''
    reads records from JSON Line file
    @param f_name : path to file which has extracted document content 
    '''
    print('reading from %s' % f_name)
    with open(f_name) as recs:
        recs = map(lambda x: json.loads(x), recs)
        for rec in recs:
            yield {
                'doc_id': ''.join(rec['file'].split('/')[-1].split(".")[:-1]),
                # Capitalize first letter of each word in the title
                'title': string.capwords(rec['metadata'].\
                                             get('grobid:header_Title', '')),
                'authors': rec['metadata'].get('grobid:header_Authors', ''),
                'primaryauthor': '',
                'affiliation': rec['metadata'].\
                    get('grobid:header_FullAffiliations', ''),
                'venue': '',
                'year': '',
                'doc_url': '',
                'content': rec['content'].strip(),
            }

if __name__ == '__main__':
    parser = ArgumentParser(description='Inserts documents to PSQL table',
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("-docs", help="Path to jsonline file having parsed data", required=True)
    parser.add_argument("-txts", help="Path to extracted .txt files", required=True)
    parser.add_argument("-idprefix", help="ID prefix. Example:lpsc15-", required=True)
    parser.add_argument("-table", help="table name for insertion", default='documents')
    parser.add_argument("-db", help="database name for insertion", default='mte')
    parser.add_argument("-user", help="DB user name", default=os.environ['USER'])
    args = vars(parser.parse_args())
    docs = get_records(args['docs'])

    idprefix = args['idprefix']
    print("Id Prefix %s" % idprefix)

    if 'lpsc' in idprefix:
        # Construct the URL for LPSC docs
        print 'Constructing URLs for LPSC docs.'
        def construct_doc_url(rec, prefix=idprefix):
            rec['doc_url'] = 'http://www.hou.usra.edu/meetings/' + \
                ('lpsc20%s/pdf/' % prefix[4:6]) + \
                rec['doc_id'] + '.pdf'
            return rec
        docs = map(construct_doc_url, docs)

        # Add venue and year
        def update_doc_venue_year(rec, prefix=idprefix):
            rec['venue'] = 'Lunar and Planetary Science Conference, ' + \
                ('Abstract #%s' % rec['doc_id'])
            rec['year'] = 2000 + int(prefix[4:6])
            return rec
        docs = map(update_doc_venue_year, docs)

    # Add the text content.  GROBID extracted this too,
    # but we need it to be consistent with our annotations
    # and offsets.  So we'll use our .txt instead.
    def update_doc_content(rec, txtdir=args['txts']):
        txtfile = os.path.join(txtdir, rec['doc_id'] + '.txt')
        txtf = open(txtfile, 'r')
        rec['content'] = txtf.read()
        txtf.close()
        return rec
    docs = map(update_doc_content, docs)

    # Add the primary author.
    # Heuristic: first phrase in 'authors' consisting of words longer than 1 char
    def update_primary_author(rec):
        au = rec['authors']
        auwords = au.split()
        pa = ''
        in_last_name = False
        for auw in auwords:
            if len(auw) > 1:
                if in_last_name:
                    pa += (' ' + auw)
                else:
                    pa = auw
                    in_last_name = True
            else:
                if in_last_name:  # Done!
                    break
        rec['primaryauthor'] = pa
        return rec
    docs = map(update_primary_author, docs)

    # Add the document id prefix (e.g., lpsc15)
    def update_doc_id(rec, prefix=idprefix):
        rec['doc_id'] = prefix + rec['doc_id']
        return rec
    docs = map(update_doc_id, docs)

    # Check/fill in missing titles and authors
    for rec in docs:
        for field in ['title', 'authors']:
            if rec[field] == '':
                rec[field] = 'Unknown'


    with PSQLDb(args['db'], args['user']) as db:
        count = db.insert_all(args['table'], docs)
        print("Inserted %d records to %s" % (count, args['table']))


# Copyright 2016, by the California Institute of Technology. ALL
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
