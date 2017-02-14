#!/usr/local/bin/python

import cgi, cgitb
import json
import sys

try:
    import psycopg2
    import psycopg2.extras
except ImportError, e:
    print "The Python module psycopg2 could not be imported, so ",
    print "we cannot access the MTE SQL database."
    sys.exit()

cgitb.enable()

sys.stdout.write("Content-Type: application/json")
sys.stdout.write("\n")
sys.stdout.write("\n")

connection = psycopg2.connect("dbname='mte' user='mtedbuser' host='127.0.0.1' password='Fraz=ev2'")
cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

parameters = cgi.FieldStorage()
searchStr = parameters.getvalue("searchStr")
#searchStr = "bardin_bluff"

sql_target = "select distinct target_name from targets where lower(target_name) = '%s'" % (searchStr)
sql_target_by_component_name = "select distinct target_name from contains where lower(component_name) = '%s'" % (searchStr)
sql_target_by_primaryauthor = "select distinct target_name from contains, documents where contains.doc_id = documents.doc_id and lower(primaryauthor)='%s'" % (searchStr)

target_list = []
results = []
return_dic = {}
row = [0] * 10

try: 
    cursor.execute(sql_target)
    target_name = cursor.fetchall()
    target_list.extend(target_name)

    cursor.execute(sql_target_by_component_name)
    target_name = cursor.fetchall()
    target_list.extend(target_name)

    cursor.execute(sql_target_by_primaryauthor)
    target_name = cursor.fetchall()
    target_list.extend(target_name)

    for target_name in target_list: 
        targetName = target_name[0]
        sql_targets_an = "select target_id, target_first_sol from targets_an where target_name = '%s'" % (target_name[0])
        cursor.execute(sql_targets_an);
        records = cursor.fetchall()
        if not records:
            targetId = "None"
            targetFirstSol = "None"
        else:
            targetId = records[0][0]
            targetFirstSol = records[0][1]

        sql_contains = "select doc_id, contains.component_name, excerpt, component_label from contains, components where target_name = '%s' and (component_label='Element' or component_label='Feature' or component_label='Material' or component_label='Mineral') and contains.component_name = components.component_name order by case component_label when 'Element' then 1 when 'Mineral' then 2 when 'Material' then 3 when 'Feature' then 4 else 5 end;" % (target_name[0])
        cursor.execute(sql_contains)
        records = cursor.fetchall() 
        for record in records:
            sql_documents = "select primaryauthor, title, year, venue, doc_url from documents where doc_id = '%s'" % (record[0])
            cursor.execute(sql_documents)
            doc_result = cursor.fetchall()
            componentName = record[1]
            authors = doc_result[0][0]
            title = doc_result[0][1]
            excerpt = record[2]
            componentLabel = record[3]
            year = doc_result[0][2]
            venue = doc_result[0][3]
            docUrl = doc_result[0][4]
            #results.append([targetName, targetId, targetFirstSol, componentName, componentLabel, authors, title, excerpt, year, venue, docUrl, targetLat, targetLon])
            results.append([targetName, targetId, targetFirstSol, componentName, componentLabel, authors, title, excerpt, year, venue, docUrl])
    return_dic["results"] = results
except:
    return_dic["results"] = ""

sys.stdout.write(json.dumps(return_dic))
sys.stdout.write("\n")

cursor.close()
connection.close()
sys.stdout.close()
