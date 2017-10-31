#!/usr/bin/env python
# 
# Query Solr server for MTE documents and allow user to interactively
# review/edit the title, authors, etc.
#
# Author: Kiri Wagstaff
# October 26, 2017
# Copyright notice at bottom of file.

import sys, os
import re
# Default readline doesn't support startup or pre-input-hooks.
# import readline
# https://stackoverflow.com/questions/28732808/python-readline-module-on-os-x-lacks-set-pre-input-hook
import gnureadline as readline
import pysolr

solrserver = 'http://localhost:8983/solr/docsdev/'

# Query Solr server for all MTE docs
s = pysolr.Solr(solrserver)
# This syntax was unintuitive and not documented
docs = s.search(q='id:lpsc15-1372', fq='type:doc')

# Iterate through docs to find ones that need review.
for d in docs:
    print d['id']

    # If "old_title" field is non-empty, skip this document.
    # Actually, no way to do this unless I updated the schema and restart Solr.
    if 'old_title' in d.keys() and d['old_title'] != '':
        continue

    # Show first few lines of 'content' for context.
    print d['content'][:200].strip()

    if 'old_title' in d.keys():
        print d['old_title']
    print '<%s>' % d['title']

    # Prompt user to view/edit desired values.
    # Title, authors, primaryauthor (+ venue, year?)
    # If venue does not exist, try to pre-populate with a guess based on id (LPSC)

    default_title = d['title']
    # If title is Unknown, try to guess it from content.
    if default_title == 'Unknown':
        default_title = re.search(r'[^\.]+\.[^\.\n]+\n+([^\.]+)\.', 
                                  d['content']).group(1).title()

    readline.set_startup_hook(lambda: readline.insert_text(default_title))

    #d['old_title'] = d['title']
    new_title = raw_input('Title: ')

    #print d['old_title']
    #print d['title']

    if new_title != d['title']:
        print 'Updating Solr.'
        d['title'] = new_title
        # This also seems to commit by default, yay.
        s.add([d], fieldUpdates={'title':'set'})


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
