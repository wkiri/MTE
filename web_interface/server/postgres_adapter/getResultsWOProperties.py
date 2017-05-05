#!/usr/local/bin/python

import cgi, cgitb
import json
import sys

try:
    import psycopg2
    HAVE_psycopg2 = True
except ImportError, e:
    print "The Python module psycopg2 could not be imported, so ",
    print "we cannot access the MTE SQL database."
    sys.exit()

cgitb.enable()

sys.stdout.write("Content-Type: application/json")
sys.stdout.write("\n")
sys.stdout.write("\n")

parameters = cgi.FieldStorage()
searchStr = parameters.getvalue("searchStr");
#searchStr = "bardin_bluff"

sql = "select targets.target_name, target_id, target_first_sol from targets, targets_an where LOWER(targets.target_name) like LOWER('%s') and LOWER(targets.target_name) = LOWER(targets_an.target_name);" % ("%" + searchStr + "%")

connection = psycopg2.connect("dbname='mte' user='mtedbuser' host='127.0.0.1' password='Fraz=ev2'")
cursor = connection.cursor()

result = {}

try:
    cursor.execute(sql)
    rows = cursor.fetchall()

    if not rows:
        sql_targets = "select target_name from targets where LOWER(target_name) = '%s'" % (searchStr)
        cursor.execute(sql_targets)
        rows = cursor.fetchall() 
        result["results"] = rows
    else:
        result["results"] = rows
except:
    result["results"] = "error"

sys.stdout.write(json.dumps(result))
sys.stdout.write("\n")

cursor.close()
connection.close()
sys.stdout.close()
