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

document_sql = "select count(*) from documents;"
target_sql = "select count(distinct canonical) from anchors where label='Target';"
element_sql = "select count(distinct canonical) from anchors where label='Element';"
feature_sql = "select count(distinct canonical) from anchors where label='Feature';"
material_sql = "select count(distinct canonical) from anchors where label='Material';"
mineral_sql = "select count(distinct canonical) from anchors where label='Mineral';"
event_sql = "select count(distinct event_id) from contains;"

connection = psycopg2.connect("dbname='mte' user='mtedbuser' host='127.0.0.1' password='Fraz=ev2'")
cursor = connection.cursor()

result = {}

try:
    #document count
    cursor.execute(document_sql)
    count = cursor.fetchall()
    result["document_count"] = count

    #target count
    cursor.execute(target_sql)
    count = cursor.fetchall()
    result["target_count"] = count

    #event count
    cursor.execute(event_sql)
    count = cursor.fetchall()
    result["event_count"] = count

    #element count
    cursor.execute(element_sql)
    count = cursor.fetchall()
    result["element_count"] = count

    #feature count
    cursor.execute(feature_sql)
    count = cursor.fetchall()
    result["feature_count"] = count

    #material count
    cursor.execute(material_sql)
    count = cursor.fetchall()
    result["material_count"] = count

    #mineral count
    cursor.execute(mineral_sql)
    count = cursor.fetchall()
    result["mineral_count"] = count
except:
    result["error"] = "error"

sys.stdout.write(json.dumps(result))
sys.stdout.write("\n")

cursor.close()
connection.close()
sys.stdout.close()
