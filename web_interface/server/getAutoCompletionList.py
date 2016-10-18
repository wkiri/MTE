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

sql = "select canonical, label from anchors where (label='Target' or label='Element' or label='Feature' or label='Material' or label='Mineral') order by case label when 'Target' then 1 when 'Element' then 2 when 'Material' then 3 when 'Mineral' then 4 when 'Feature' then 5 else 6 end;"

connection = psycopg2.connect("dbname='mte' user='mtedbuser' host='127.0.0.1' password='Fraz=ev2'")
cursor = connection.cursor()

result = {}

try:
    cursor.execute(sql)
    rows = cursor.fetchall()
    result["results"] = rows
except:
    result["results"] = "error"

sys.stdout.write(json.dumps(result))
sys.stdout.write("\n")

cursor.close()
connection.close()
sys.stdout.close()
