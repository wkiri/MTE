#!/bin/bash
# Script to clear out the MTE DB and set everything back up

# PostgreSQL database name
DB=mte

# Delete old tables
psql -d $DB -c 'drop table contains, components, targets, documents, anchors, targets_an;'

# Create new ones
./create_db.py

# Insert the documents
./insert_docs.py -db $DB -docs ../text/lpsc15-sol707.jsonl  -txts ../text/lpsc15-C-raymond-sol707  -idprefix lpsc15- 2>/dev/null
./insert_docs.py -db $DB -docs ../text/lpsc15-sol1159.jsonl -txts ../text/lpsc15-C-raymond-sol1159 -idprefix lpsc15- 2>/dev/null
./insert_docs.py -db $DB -docs ../text/lpsc16.jsonl -txts ../text/lpsc16-C-pre-annotate -idprefix lpsc16- 2>/dev/null

# Add the content from .ann files
./update_db.py -db $DB -anns ../text/lpsc15-C-raymond-sol707  -idprefix lpsc15- 2>/dev/null
./update_db.py -db $DB -anns ../text/lpsc15-C-raymond-sol1159 -idprefix lpsc15- 2>/dev/null
./update_db.py -db $DB -anns ../text/lpsc16-C-raymond -idprefix lpsc16- 2>/dev/null

# Add the Analyst's Notebook table
./insert_an.py -db $DB 2>/dev/null

# Check that it worked
echo 'Documents:'
psql -d $DB -c 'SELECT COUNT(*) from documents;'
echo 'Targets:'
psql -d $DB -c 'SELECT COUNT(*) from targets;'
echo 'Components:'
psql -d $DB -c 'SELECT COUNT(*) from components;'
echo 'Contains:'
psql -d $DB -c 'SELECT COUNT(*) from contains;'
echo 'Anchors:'
psql -d $DB -c 'SELECT COUNT(*) from anchors;'
echo 'Targets_AN:'
psql -d $DB -c 'SELECT COUNT(*) from targets_an;'
