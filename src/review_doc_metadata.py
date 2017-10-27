#!/usr/bin/env python
# 
# Query Solr server for MTE documents and allow user to interactively
# review/edit the title, authors, etc.
#
# Author: Kiri Wagstaff
# October 26, 2017
# Copyright notice at bottom of file.

import sys, os
# Default readline doesn't support startup or pre-input-hooks.
# import readline
# https://stackoverflow.com/questions/28732808/python-readline-module-on-os-x-lacks-set-pre-input-hook
import gnureadline as readline
import json
import urllib2
import requests

solrserver = 'http://localhost:8983/solr/docsdev/'

# Query Solr server for all MTE docs
connection = urllib2.urlopen(solrserver + 'query?q=id:lpsc15-1373&fq=type:doc')
response = json.load(connection)
print response['response']['numFound'], 'docs found.'

# This does not return JSON format
#resp = requests.get(solrserver + 'select',
#                    params={'q':'id:lpsc15-1373'})
#print resp.get('response').get('numFound'), 'docs found.'


# Iterate through docs to find ones that need review.
for d in response['response']['docs']:
    print d['id']

    # If "old_title" field is non-empty, skip this document.
    if 'old_title' in d.keys() and d['old_title'] != '':
        continue

    if 'old_title' in d.keys():
        print d['old_title']
    print '<%s>' % d['title']

    # Show first few lines of 'content' for context.

    # Prompt user to view/edit desired values.
    # Title, authors, primaryauthor (+ venue, year?)
    # If venue does not exist, try to pre-populate with a guess based on id (LPSC)
    readline.set_startup_hook(lambda: readline.insert_text(d['title']))

    d['old_title'] = d['title']
    d['title']     = raw_input('Title: ')

    print d['old_title']
    print d['title']

    # Update it in Solr
    print solrserver + 'update/json?commit=true'
    #req = urllib2.Request(url=solrserver + 'update/json?commit=true',
    #req = urllib2.Request(url=solrserver + 'update/json/docs',
    #req = urllib2.Request(url=solrserver + 'update/json/docs?commit=true',
    #                      data=json.dumps(d))
    #req.add_header('Content-type', 'application/json')
    #f = urllib2.urlopen(req)

    # Thist posting fails, but I don't know why
    resp = requests.post(solrserver + 'update/json?commit=true',
                         data=json.dumps(d).encode('utf-8', 'replace'),
                         headers={"content-type": "application/json"})
    if not resp or resp.status_code != 200:
        print('Solr posting failed:', resp)
    

# Copyright 2017, by the California Institute of Technology. ALL
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
