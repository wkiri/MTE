#!/usr/bin/env python
# update_db.py
# Mars Target Encyclopedia
# Read in brat annotations and update the MTE PostgreSQL database.
#
# Kiri Wagstaff
# January 12, 2016
# Copyright notice at bottom of file.

import sys, os
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from brat_annotation import BratAnnotation

# Import the Python module psycopg2 to enable direct connections to 
# the PostgreSQL database.
try:
    import psycopg2
    HAVE_psycopg2 = True
except ImportError, e:
    print "The Python module psycopg2 could not be imported, so ",
    print "we cannot access the MTE SQL database."
    sys.exit()


def update_db(args):

    # Connect to the DB
    connection = psycopg2.connect("dbname=%s user=%s" % (args['db'], args['user']))
    cursor     = connection.cursor()

    dirlist = [fn for fn in os.listdir(args['anns']) if
               fn.endswith('.ann')]

    print 'Inserting brat annotations into the MTE from %d files in %s.' % \
        (len(dirlist), args['anns'])

    for fn in dirlist:
        fullname = args['anns']+'/'+fn

        # Skip empty files
        if os.stat(fullname).st_size == 0:
            continue

        doc_id = args['idprefix'] + fn[:-4]

        # Skip this document if already processed
        cursor.execute("SELECT EXISTS(SELECT * FROM contains WHERE doc_id = '%s')" % doc_id)
        doc_processed = cursor.fetchone()[0]
        if doc_processed:
            continue

        print fn

        # Two passes because 'contains' refers to targets and components that need to
        # already have been stored.

        # Pass 1: add all anchors, targets, and components
        with open(fullname, 'r') as f:
            for line in f.readlines():
                # Skip events and relations
                if (line[0] == 'E' or line[0] == 'R'):
                    continue
                b = BratAnnotation(line, doc_id, 'raymond')
                b.insert(cursor)

        connection.commit()

        # Pass 2: add all events and relations
        with open(fullname, 'r') as f:
            for line in f.readlines():
                # Keep events and relations
                if (line[0] != 'E' and line[0] != 'R'):
                    continue
                b = BratAnnotation(line, doc_id, 'raymond')
                b.insert(cursor)
            
        connection.commit()

    cursor.close()
    connection.close()


if __name__ == '__main__':
    parser = ArgumentParser(description='Adds annotations to PSQL DB',
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("-anns", help="Path to .ann files", required=True)
    parser.add_argument("-db", help="Database name for insertion", default='mte')
    parser.add_argument("-idprefix", help="ID prefix. Example:lpsc15-", required=True)
    parser.add_argument("-user", help="Database user name", default=os.environ['USER'])
    args = vars(parser.parse_args())
    update_db(args)


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