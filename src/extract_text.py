#!/usr/bin/env python
# extract_text.py
# Extract text strings from PDF files using Tika
# and write them out in .txt form. 
#
# Kiri Wagstaff
# June 16, 2015

import sys, os
import re
import tika

from tika import parser

# Local files
textdir = '../pdfs/lpsc15-pdfs'

dirlist = [fn for fn in os.listdir(textdir) if
           fn.endswith('.pdf')]

print 'Extracting text, using Tika, from %d files in %s.' % \
    (len(dirlist), textdir)

for fn in dirlist:
    print fn
    parsed = parser.from_file(textdir + '/' + fn)

    with open(textdir + '/' + fn[0:-4] + '.txt', 'w') as outf:
        # Remove non-ASCII characters
        cleaned = re.sub(r'[^\x00-\x7F]+',' ', parsed['content'])
        # Replace multiple spaces with a single one
        #cleaned = re.sub(r'[ ]+',' ', cleaned)
        # Replace multiple newlines with a single one
        cleaned = re.sub(r'[\n]+','\n', cleaned)
        cleaned = re.sub(r' \n',' ', cleaned)
        cleaned = re.sub(r'  ','\n', cleaned)
        # Remove hyphenation
        cleaned = cleaned.replace('-\n','')
        outf.write(cleaned)
        outf.close()
