#!/usr/bin/env python
# pre_annotate.py
# Annotate target names and elements in .txt files;
# write them out in brat .ann form.
#
# Kiri Wagstaff
# February 18, 2016

import sys, os
import string
import re

# Input files
textdir = '../text/lpsc15-C'

# Reference files
elementfile = '../ref/elements.txt'

# Files to analyze
dirlist = [fn for fn in os.listdir(textdir) if
           fn.endswith('.txt')]

# Process lines from input file, annotate anything that matches 'items',
# and write out the annotations to outf with type 'name'.
def pre_annotate(lines, items, name, outf):
    # Initialize counters
    target_ind = 1
    span_start = 0
    span_end = 0

    # Iterate through documents; output to .ann file
    with open(annfile, 'w') as outf:
        # Iterate through words and look for a match in the elements list
        for l in lines:
            # Specifying ' ' explicitly means that all single spaces
            # will cause a split.  This way we can update span_start
            # correctly even if there are multiple spaces present.
            words = l.split(' ')
            for w in words:
                # Remove any trailing \n etc.
                w_strip = w.strip()
                # Remove any punctuation
                w_strip = re.sub('[%s]' % re.escape(string.punctuation), 
                                 '', w_strip)
                if w_strip in items:
                    # This handles leading and trailing punctuation,
                    # but not cases where there is internal punctuation
                    span_start_strip = span_start + w.index(w_strip)
                    #print str(w.index(w_strip))
                    span_end    = span_start_strip + len(w_strip) 
                    # Format: Tx\tTarget <span_start> <span_end>\t<word>
                    outf.write('T' + str(target_ind) + '\t' +
                               name + ' ' + str(span_start_strip) + 
                               ' ' + str(span_end) + '\t' +
                               w_strip + '\n')
                    # Set up for the next target
                    target_ind += 1
                else:
                    span_end    = span_start + len(w_strip) 
                    
                #print '<%s>, span %d to %d' % (w, span_start, span_end)
                # Either way, update span_start
                span_end   = span_start + len(w)
                span_start = span_end + 1 # Assumes followed by space 
                # (or newline, for final word in line)
            span_start -= 1 # Uncount the newline (double-count)


##########################################################

print 'Annotating elements in %d files from %s.' % \
    (len(dirlist), textdir)

# Read in the elements files
with open(elementfile, 'r') as inf:
    lines = inf.readlines()
    elements = [l.strip() for l in lines]
    # Add lower-case versions of long element names
    elements += [e.lower() for e in elements if len(e) > 2]
    
print elements

for fn in dirlist:
    print fn

    # Read in the input .txt document
    with open(textdir + '/' + fn, 'r') as inf:
        lines = inf.readlines()

    annfile = textdir + '/' + fn[0:-4] + '.ann'

    # Create the annotations
    with open(annfile, 'w') as outf:
        pre_annotate(lines, elements, 'Element', outf)

#    sys.exit(0)
    

