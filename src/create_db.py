#!/usr/bin/env python
# create_db.py
# Mars Target Encyclopedia
# Create the postgresql database.
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

# Connect to the DB
try:
    user = os.environ['USER']
    connection = psycopg2.connect("dbname=mte user=%s" % user)
    cursor     = connection.cursor()

    print 'Checking for existence of MTE databases; '
    print ' will create them if needed.'
    print ' (No output means they already exist.)'

    # If tables don't exist, create them

    # -------- targets -----------
    # Table of canonical target names
    cursor.execute("SELECT EXISTS(SELECT * FROM information_schema.tables " +
                   "WHERE table_name='targets')")
    table_exists = cursor.fetchone()[0]
    if not table_exists:
        print "Creating the targets table from scratch."
        create_table_cmd  = "CREATE TABLE targets ("
        create_table_cmd += " target_name       varchar(80) PRIMARY KEY"
        create_table_cmd += ");"
        cursor.execute(create_table_cmd)

    # -------- targets_an -----------
    # Table of information from the Analyst's Notebook
    # Could potentially be merged with the targets table,
    # but since the targets table is currently inferred from the text,
    # it is incomplete.  For now we'll keep them separate.
    cursor.execute("SELECT EXISTS(SELECT * FROM information_schema.tables " +
                   "WHERE table_name='targets_an')")
    table_exists = cursor.fetchone()[0]
    if not table_exists:
        print "Creating the Analyst's Notebook targets table from scratch."
        create_table_cmd  = "CREATE TABLE targets_an ("
        create_table_cmd += " target_name       varchar,"
        # Internal AN target id ('anPlaceID')
        create_table_cmd += " target_id         integer PRIMARY KEY,"
        # Sol on which the target was defined
        create_table_cmd += " target_first_sol  integer"
        create_table_cmd += ");"
        cursor.execute(create_table_cmd)

    # -------- components -----------
    cursor.execute("SELECT EXISTS(SELECT * FROM information_schema.tables " +
                   "WHERE table_name='components')")
    table_exists = cursor.fetchone()[0]
    if not table_exists:
        print "Creating the components table from scratch."
        create_table_cmd  = "CREATE TABLE components ("
        create_table_cmd += " component_name       varchar(80) PRIMARY KEY,"
        create_table_cmd += " component_label      varchar(80)"
        create_table_cmd += ");"
        cursor.execute(create_table_cmd)

    # -------- documents -----------
    DOCUMENTS_TABLE_STATEMENT = '''CREATE TABLE IF NOT EXISTS documents (
        doc_id          VARCHAR(100) PRIMARY KEY,
        title           VARCHAR(1024),
        authors         VARCHAR(4096),
        primaryauthor   VARCHAR(1024),
        affiliation     TEXT,
        venue           TEXT,
        year            INTEGER,
        doc_url         VARCHAR(1024),
        content         TEXT
    );'''
    cursor.execute(DOCUMENTS_TABLE_STATEMENT)

    # -------- anchors -----------
    # One entry for each text annotation covering the text that anchors it
    cursor.execute("SELECT EXISTS(SELECT * FROM information_schema.tables " +
                   "WHERE table_name='anchors')")
    table_exists = cursor.fetchone()[0]
    if not table_exists:
        print "Creating the anchors table from scratch."
        create_table_cmd  = "CREATE TABLE anchors ("
        # anchor_id could match target_id, component_id, or event_id
        create_table_cmd += " anchor_id         varchar(100) PRIMARY KEY,"
        create_table_cmd += " label             varchar(20),"
        create_table_cmd += " canonical         text,"
        create_table_cmd += " text              text,"
        create_table_cmd += " span_start        integer,"
        create_table_cmd += " span_end          integer"
        create_table_cmd += ");"
        cursor.execute(create_table_cmd)

    # -------- contains -----------
    cursor.execute("SELECT EXISTS(SELECT * FROM information_schema.tables " +
                   "WHERE table_name='contains')")
    table_exists = cursor.fetchone()[0]
    if not table_exists:
        print "Creating the contains table from scratch."
        create_table_cmd  = "CREATE TABLE contains ("
        create_table_cmd += " event_id          varchar(100),"
        create_table_cmd += " doc_id            varchar(100) REFERENCES documents,"
        create_table_cmd += " anchor_id         varchar(100) REFERENCES anchors,"
        create_table_cmd += " target_name       varchar(80) REFERENCES targets,"
        create_table_cmd += " component_name    varchar(80) REFERENCES components,"
        create_table_cmd += " magnitude         varchar(10),"
        create_table_cmd += " confidence        varchar(10),"
        create_table_cmd += " annotator         varchar(100),"
        create_table_cmd += " excerpt           text"
        create_table_cmd += ");"
        cursor.execute(create_table_cmd)

    # Commit changes
    connection.commit()

    # Update permissions
    cursor.execute('grant select, insert, update '
                   'on contains, components, targets, documents, '
                   'anchors, targets_an '
                   'to youlu, thammegr, wkiri, ksingh;')
    cursor.execute('grant select '
                   'on contains, components, targets, documents, '
                   'anchors, targets_an '
                   'to mtedbuser;')

    # Commit changes
    connection.commit()

except psycopg2.Warning, e:
    print 'Warning: ', e
except psycopg2.Error, e:
    print 'Error: ', e
finally:
    cursor.close()
    connection.close()


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
