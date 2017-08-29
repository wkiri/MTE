#!/usr/bin/env python
# insert_mmgis.py
# Mars Target Encyclopedia
# Add information from the MMGIS (lat/lon coords ) to our MTE PostgreSQL DB.
#
# Kiri Wagstaff
# October 20, 2016
# Copyright notice at bottom of file.

import sys, os
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import string
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

# MMGIS ChemCam target database
mmgisfile = '../ref/MSL_CHEMCAM_HardTarget_Sol1311_unique_v2.csv' 

def update_mmgis(args):

    print "Inserting target information from the MMGIS target DB."
    print "File: ", mmgisfile

    # Connect to the DB
    connection = psycopg2.connect("dbname=%s user=%s" % (args['db'], args['user']))
    cursor     = connection.cursor()

    # Read in the CSV and add fields we want

    with open(mmgisfile, 'r') as csvfile:
        csvfile.readline()  # Consume the header
        mmgisreader = csv.reader(csvfile)
        for row in mmgisreader:

            # Convert target name into canonical form
            s = row[2]
            s = string.replace(s, '_', ' ')
            s = string.capwords(s)
            s = s.replace(' ', '_')
            target_name = s

            dbutils.insert_into_table(cursor=cursor,
                                      table='targets_mmgis',
                                      columns=['target_name',
                                               'target_latitude',
                                               'target_longitude'],
                                      values=[s,
                                              float(row[7]),
                                              float(row[8])])

        connection.commit()

    cursor.close()
    connection.close()


if __name__ == '__main__':
    parser = ArgumentParser(description="Adds MMGIS target lat/lon table to PSQL DB",
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("-db", help="Database name for insertion", default='mte')
    parser.add_argument("-user", help="Database user name", default=os.environ['USER'])
    args = vars(parser.parse_args())
    update_mmgis(args)


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
