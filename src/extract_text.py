#!/usr/bin/env python
# extract_text.py
# Extract text strings from PDF files using Tika
# and write them out in .txt form. 
#
# Kiri Wagstaff
# June 16, 2015
# Copyright notice at bottom of file.

import sys, os
import re
import tika

from tika import parser

# Local files
#pdfdir  = '../text/lpsc15-pdfs'
#textdir = '../text/lpsc15-all'
pdfdir  = '../text/lpsc16-pdfs'
textdir = '../text/lpsc16-all'

dirlist = [fn for fn in os.listdir(pdfdir) if
           fn.endswith('.pdf')]

print 'Extracting text, using Tika, from %d files in %s.' % \
    (len(dirlist), pdfdir)
print '  Writing output text files to %s.' % textdir

for fn in dirlist:
    print fn
    parsed = parser.from_file(pdfdir + '/' + fn)

    if parsed['content'] == None:
        print 'Tika found no content in %s.' % fn
        continue

    with open(textdir + '/' + fn[0:-4] + '.txt', 'w') as outf:
        # Remove non-ASCII characters
        cleaned = re.sub(r'[^\x00-\x7F]+',' ', parsed['content'])
        # Replace multiple spaces with a single one
        #cleaned = re.sub(r'[ ]+',' ', cleaned)
        # Remove hyphenation
        cleaned = cleaned.replace('-\n','')
        # Remove single newlines
        cleaned = re.sub(r'(?<!\n)\n(?!\n)','',cleaned)
                         #r'\n[^\n]','', cleaned)
        # Replace multiple newlines with a single one
        cleaned = re.sub(r'[\n]+','\n', cleaned)
        cleaned = re.sub(r'[ ]+',' ', cleaned)
        outf.write(cleaned)
        outf.close()


# Copyright 2015, by the California Institute of Technology. ALL
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
