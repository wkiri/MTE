#!/usr/bin/env python
# insert_an.py
# Mars Target Encyclopedia
# Add information from the Analyst's Notebook to our MTE PostgreSQL DB.
#
# Kiri Wagstaff
# August 30, 2016

import sys, os
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

print "Inserting target information from the Analyst's Notebook."
print "File: ", anfile

# Connect to the DB
user = os.environ['USER']
connection = psycopg2.connect("dbname=mte user=%s" % user)
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
