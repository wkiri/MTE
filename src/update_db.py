#!/usr/bin/env python
# update_db.py
# Mars Target Encyclopedia
# Read in brat annotations and update the MTE PostgreSQL database.
#
# Kiri Wagstaff
# January 12, 2016

import sys, os
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

# Local files
#textdir = '../text/lpsc15-A'
#textdir = '../text/lpsc15-C-raymond-sol707'
textdir = '../text/lpsc15-C-raymond-sol1159'
source  = 'lpsc15'

dirlist = [fn for fn in os.listdir(textdir) if
           fn.endswith('.ann')]

print 'Inserting brat annotations into the MTE from %d files in %s.' % \
    (len(dirlist), textdir)

# Connect to the DB
user = os.environ['USER']
connection = psycopg2.connect("dbname=mte user=%s" % user)
cursor     = connection.cursor()

for fn in dirlist:
    fullname = textdir+'/'+fn

    # Skip empty files
    if os.stat(fullname).st_size == 0:
        continue

    doc_id = source + '-' + fn[:-4]

    # Skip this document if already processed
    cursor.execute("SELECT EXISTS(SELECT * FROM contains WHERE doc_id = '%s')" % doc_id)
    doc_processed = cursor.fetchone()[0]
    if doc_processed:
        continue

    print fn

    # Two passes because 'contains' refers to targets and components that need to
    # already have been stored.

    # Pass 1: add all targets and components
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
