# dbutils.py
# Mars Target Encyclopedia
# PostgreSQL database utilities for easy insertion.
#
# Kiri Wagstaff
# January 12, 2016

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


