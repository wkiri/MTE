#!/usr/bin/env python
# insert_an.py
# Mars Target Encyclopedia
# Add information from the Analyst's Notebook to our MTE PostgreSQL DB.
#
# Kiri Wagstaff
# August 30, 2016
# Copyright notice at bottom of file.

import sys, os
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import csv
import dbutils

# Import the Python module psycopg2 to enable direct connections to 
# the PostgreSQL database.
try:
    import psycopg2
    HAVE_psycopg2 = True
except ImportError, e:
    print "The Python module psycopg2 could not be imported, so ",
    print "we cannot access the MTE SQL database."
    sys.exit()

# Analyst's Notebook database
anfile = '../ref/2016-0816-MSL-AN-Target-table.csv'

def update_an(args):

    print "Inserting target information from the Analyst's Notebook."
    print "File: ", anfile

    # Connect to the DB
    connection = psycopg2.connect("dbname=%s user=%s" % (args['db'], args['user']))
    cursor     = connection.cursor()

    # Read in the CSV and add fields we want

    with open(anfile, 'r') as csvfile:
        csvfile.readline()  # Consume the header
        anreader = csv.reader(csvfile)
        for row in anreader:
            dbutils.insert_into_table(cursor=cursor,
                                      table='targets_an',
                                      columns=['target_name',
                                               'target_id',
                                               'target_first_sol'],
                                      values=[row[8],
                                              int(row[0]),
                                              int(row[16])])

        connection.commit()

    cursor.close()
    connection.close()


if __name__ == '__main__':
    parser = ArgumentParser(description="Adds Analyst's Notebook table to PSQL DB",
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("-db", help="Database name for insertion", default='mte')
    parser.add_argument("-user", help="Database user name", default=os.environ['USER'])
    args = vars(parser.parse_args())
    update_an(args)


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
