#!/usr/bin/env python
# extract_text.py
# Extract text strings from PDF files using Tika
# and write them out in .txt form. 
#
# Kiri Wagstaff
# June 16, 2015

import sys, os, io
import re
import tika

from tika import parser

# Local files
#pdfdir  = '../text/lpsc14-pdfs'
#textdir = '../../MTE-corpus/lpsc14-text'
#pdfdir  = '../text/lpsc15-pdfs'
#textdir = '../../MTE-corpus/lpsc15-text'
#textdir = '../text/lpsc15-all'
pdfdir  = '../text/lpsc16-pdfs'
textdir = '../../MTE-corpus/lpsc16-text'
#textdir = '../text/lpsc16-all'

dirlist = [fn for fn in os.listdir(pdfdir) if
           fn.endswith('.pdf')]

print 'Extracting text, using Tika, from %d files in %s.' % \
    (len(dirlist), pdfdir)
print '  Writing output text files to %s.' % textdir

if not os.path.exists(textdir):
    os.mkdir(textdir)

for fn in dirlist:
    print fn
    parsed = parser.from_file(pdfdir + '/' + fn)

    if parsed['content'] == None:
        print 'Tika found no content in %s.' % fn
        continue

    with io.open(textdir + '/' + fn[0:-4] + '.txt', 'w', encoding='utf8') as outf:
        cleaned = parsed['content']

        # Translate some UTF-8 punctuation to ASCII
        punc = { 0x2018:0x27, 0x2019:0x27, # single quote
                 0x201C:0x22, 0x201D:0x22, # double quote
                 0x2010:0x2d, 0x2011:0x2d, 0x2012:0x2d, 0x2013:0x2d, # hyphens
                 0xFF0C:0x2c, # comma
                 0x00A0:0x20, # space
                 0x2219:0x2e, 0x2022:0x2e, # bullets
                 }
#                 0x005E:0x5e, 0x02C6:0x5e, 0x0302:0x5e, 0x2038:0x5e, # carets
#                 0x00B0:0x6f, 0x02DA:0x6f, # degree
#                 0x00B9:0x31, 0x00B2:0x32, 0x00B3:0x33, # exponents
        cleaned = cleaned.translate(punc)

        # Remove hyphenation at the end of lines 
        # (this is sometimes bad, as with "Fe-\nrich")
        cleaned = cleaned.replace('-\n','\n')

        # Remove all newlines
        cleaned = re.sub(r'[\r|\n]+','', cleaned)

        # Stick newlines back in after xxxx.PDF and xxxx.pdf
        cleaned = re.sub(r'([0-9][0-9][0-9][0-9].PDF)', '\\1\n', cleaned,
                         flags=re.IGNORECASE)
        # And "Lunar and Planetary Science Conference (201x)"
        cleaned = re.sub(r'(Lunar and Planetary Science Conference \(201[0-9]\))', 
                         '\\1\n', cleaned,
                         flags=re.IGNORECASE)

        outf.write(cleaned)
        outf.close()

