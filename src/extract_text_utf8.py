#!/usr/bin/env python
# extract_text.py
# Extract text strings from PDF files using Tika
# and write them out in .txt form. 
#
# Kiri Wagstaff
# June 16, 2015
# Copyright notice at bottom of file.

import sys, os, io
import re
import tika
tika.TikaClientOnly = True
from tika import parser
from progressbar import ProgressBar, ETA, Bar, Percentage

def main(pdfdir, textdir):

    dirlist = [fn for fn in os.listdir(pdfdir) if
               fn.endswith('.pdf')]

    print 'Extracting text, using Tika, from %d files in %s.' % \
        (len(dirlist), pdfdir)
    print '  Writing output text files to %s.' % textdir

    if not os.path.exists(textdir):
        os.mkdir(textdir)

    widgets = ['Files (of %d): ' % len(dirlist), Percentage(), ' ', Bar('='), ' ', ETA()]
    pbar = ProgressBar(widgets=widgets, maxval=len(dirlist)).start()
    
    for (i, fn) in enumerate(dirlist):
        pbar.update(i)
        #if int(fn.split('.')[0]) != 1001:
        #    continue
        #print fn
        parsed = parser.from_file(pdfdir + '/' + fn)

        try:
            if parsed['content'] == None:
                print 'Tika found no content in %s.' % fn
                import pdb; pdb.set_trace()
                continue
        except:
            print 'Tika could not parse %s.' % fn
            continue

        with io.open(textdir + '/' + fn[0:-4] + '.txt', 'w', 
                     encoding='utf8') as outf:
            cleaned = parsed['content']

            # Translate some UTF-8 punctuation to ASCII
            punc = { 0x2018:0x27, 0x2019:0x27, # single quote
                     0x201C:0x22, 0x201D:0x22, # double quote
                     0x2010:0x2d, 0x2011:0x2d, 0x2012:0x2d, 0x2013:0x2d, # hyphens
                     0xF0B0:0xb0, # degree
                     0xFF0C:0x2c, # comma
                     0x00A0:0x20, # space
                     0x2219:0x2e, 0x2022:0x2e, # bullets
                 }
            # 0x005E:0x5e, 0x02C6:0x5e, 0x0302:0x5e, 0x2038:0x5e, # carets
            # 0x00B0:0x6f, 0x02DA:0x6f, # degree
            # 0x00B9:0x31, 0x00B2:0x32, 0x00B3:0x33, # exponents
            cleaned = cleaned.translate(punc)

            # Replace newlines that separate words with a space (unless hyphen)
            cleaned = re.sub(r'([^\s-])[\r|\n]+([^\s])','\\1 \\2', cleaned)

            # Remove hyphenation at the end of lines 
            # (this is sometimes bad, as with "Fe-\nrich")
            cleaned = cleaned.replace('-\n','\n')

            # Remove all newlines
            cleaned = re.sub(r'[\r|\n]+','', cleaned)

            # Remove xxxx.PDF
            cleaned = re.sub(r'([0-9][0-9][0-9][0-9].PDF)', '', cleaned,
                             flags=re.IGNORECASE)
            # And "xx(th|st) Lunar and Planetary Science Conference ((19|20)xx)"
            # with optional parentheses, optional LPI contrib
            cleaned = re.sub(r'([0-9][0-9].. Lunar and Planetary Science Conference \(?(19|20)[0-9][0-9]\)?)( \(LPI Contrib. No. [0-9][0-9][0-9][0-9]\))? ?',
                             '', cleaned,
                             flags=re.IGNORECASE)
            # And "Lunar and Planetary Science XXXIII (2002)"
            # with Roman numeral and optional year
            cleaned = re.sub(r'(Lunar and Planetary Science [CDILVXM]+( \((19|20)[0-9][0-9]\))?) ?', 
                             '', cleaned,
                             flags=re.IGNORECASE)

            # Remove mailto: links
            cleaned = re.sub(r'mailto:[^\s]+','', cleaned)

            outf.write(cleaned)
            outf.close()


if __name__ == '__main__':
    import argparse
    ps = argparse.ArgumentParser(argument_default=argparse.SUPPRESS, 
                                 description='Extract (UTF-8) text from PDFs')

    ps.add_argument('pdfdir',  help='Location of PDF files to extract')
    ps.add_argument('textdir', help='Output directory for text files')
    args = ps.parse_args()
    main(**vars(args))


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
