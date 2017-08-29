# dbutils.py
# Mars Target Encyclopedia
# PostgreSQL database utilities for easy insertion.
#
# Kiri Wagstaff
# January 12, 2016
# Copyright notice at bottom of file.

import sys, os

# Import the Python module psycopg2 to enable direct connections to 
# the PostgreSQL database.
HAVE_psycopg2 = False
try:
    import psycopg2
    HAVE_psycopg2 = True
except ImportError, e:
    print "The Python module psycopg2 could not be imported, so ",
    print "we cannot access the MTE SQL database."
    sys.exit()


# Strongly inspired by 
# https://github.com/ryanaustincarlson/moocdb/blob/master/annotate/BratAnnotation.py
def insert_into_table(cursor, table, columns, values):
    def format_text(text):
#        return "'" + text.replace("'", "''").replace("%", "%%") + "'"
        return "'" + text.replace("'", "''") + "'"

    columns_string = "(" + ', '.join([str(c) for c in columns]) + ")" \
        if columns is not None else ""

    values_string = "(" + ', '.join([format_text(v) if type(v) in [str, unicode] else str(v) for v in values]) + ")"
    
    insert_cmd = "INSERT INTO " + table + " " + \
        columns_string + " VALUES " + values_string + ";"
    sys.stderr.write(insert_cmd + '\n')

    cursor.execute(insert_cmd)


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
