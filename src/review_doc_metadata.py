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

solrserver = 'http://localhost:8983/solr/docs/'

# Query Solr server for all MTE docs
s = pysolr.Solr(solrserver)
# This syntax was unintuitive and not documented
docs = s.search(q='id:lpsc15*', fq='type:doc', rows=1000)
#docs = s.search(q='id:lpsc16*', fq='type:doc', rows=1000)
print 'Obtained %d docs.' % len(docs)
# Sort by id
docs = sorted(docs, key=lambda d: d['id'])

fields = [('title', 'old_title_t'),
          ('authors', 'old_authors_t'),
          ('primaryauthor', 'old_primaryauthor_t')]

f, f_old = fields[2]

# Iterate through docs to find ones that need review.
for d in docs:
    print
    print d['id']

    # If "old_author_t" field is non-empty, skip this document.
    if f_old in d.keys() and d[f_old] != '':
        print '(Skipping; already edited.)'
        continue

    try:
        # Show first few lines of 'content' for context.
        print d['content'][:200].strip()
        print
    except:
        pass

    if f not in d.keys():
        d[f] = 'Unknown'

    if f == 'primaryauthor':
        print 'Authors:', d['authors']

    if f == 'authors':
        print 'Current %s: <%s>' % (f, d[f][0])
    else:
        print 'Current %s: <%s>' % (f, d[f])

    # Prompt user to view/edit desired values.
    # Title, authors, primaryauthor (+ venue, year?)
    
    default_value = d[f]
    # If title is Unknown, try to guess it from content.
    try:
        if f == 'title' and default_value == 'Unknown':
            default_value = re.search(r'[^\.]+\.[^\.\n]+\n+([^\.]+)\.', 
                                      d['content']).group(1).title()
    except:
        pass
    # Strip numbers out of authors
    if f == 'authors':
        # Note: authors is a string inside a list, hence [0]
        default_value = re.sub(r'[0-9]', '', unicode(default_value[0]))
        
        
    readline.set_startup_hook(lambda: readline.insert_text(default_value))

    new_value = raw_input('Edit the %s: ' % f)
    new_value = unicode(new_value, 'utf8')

    if new_value != d[f]:
        d[f_old] = d[f]
        print 'Updating Solr.  Hang onto your hat!'
        d[f] = new_value
        # This also seems to commit by default, yay.
        # Why don't I need to put f_old here?
        s.add([d], fieldUpdates={f:'set'})


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
