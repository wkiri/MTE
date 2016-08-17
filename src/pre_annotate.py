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
#textdir = '../text/lpsc15-C-pre-annotate-sol1159'
#textdir = '../text/lpsc15-C-pre-annotate-sol1159-v2'
textdir = '../text/lpsc16-C-pre-annotate'

# Reference files
elementfile = '../ref/elements.txt'
chemcamfile = '../ref/chemcam-targets-sol1159.txt'
mineralfile = '../ref/minerals.txt'
nonminfile  = '../ref/non-minerals.txt' # Things that end in -ite but aren't minerals
MERfile     = '../ref/MER-targets-pruned.txt'

# Remove any punctuation, except '_' and '+' (ions) and '-' 
# and '.' (e.g., Mt. Sharp)
mypunc = string.punctuation
for p in ['_', '\+', '-', '\.']:
    mypunc = re.sub(p, '', mypunc)

# Files to analyze
dirlist = [fn for fn in os.listdir(textdir) if
           fn.endswith('.txt')]

# Process lines from input file, annotate anything that matches 'items',
# and write out the annotations to outf with type 'name'.
# Number targets starting from start_t.
def pre_annotate(lines, items, name, outf, start_t):
    # Initialize counters
    target_ind = start_t
    span_start = 0
    span_end = 0

    # Iterate through words and look for a match in the item list
    for l in lines:
        # Specifying ' ' explicitly means that all single spaces
        # will cause a split.  This way we can update span_start
        # correctly even if there are multiple spaces present.
        words = l.split(' ')
        for (i,w) in enumerate(words):
            extra = 0 # Characters we stripped off but still need to count in spans
            end_of_sentence = False
            # Remove any trailing \n etc.
            w_strip = w.strip()
            #print w,w_strip
            # Track whether this is a potential end of sentence
            # to avoid spurious element abbreviation annotations
            if w_strip.endswith('.'):
                end_of_sentence = True
            #print w,w_strip
            # Remove any punctuation, except '_' and '+' (ions) and '-'
            # and '.' (e.g., Mt. Sharp)
            w_strip = re.sub('[%s]' % re.escape(mypunc), '', w_strip)
            # Try the word and also the two-word and three-word phrases it's in
            phrases = [(w, w_strip)]
            if i < len(words)-1:
                w_next_1 = re.sub('[%s]' % re.escape(mypunc), '', words[i+1])
                phrases += [(' '.join([w, words[i+1]]), ' '.join([w_strip, w_next_1]))]
            if i < len(words)-2:
                w_next_2 = re.sub('[%s]' % re.escape(mypunc), '', words[i+2])
                phrases += [(' '.join([w, words[i+1], words[i+2]]), 
                             ' '.join([w_strip, w_next_1, w_next_2]))]

            for (my_word, my_word_strip) in phrases:
                # If it ends with - or ., take it off
                if (my_word_strip.endswith('-') or 
                    my_word_strip.endswith('.')):
                    my_word_strip = my_word_strip[:-1]
                    extra   += 1
                if my_word_strip in items:
                    #print my_word, my_word_strip
                    # For elements, skip matches that end in a period
                    # and are short (i.e., abbreviations) because these
                    # are more likely to be author initials.
                    if (name == 'Element' and 
                        end_of_sentence and 
                        len(my_word_strip) <= 3):
                        span_end    = span_start + len(my_word_strip)
                    else:
                        # This handles leading and trailing punctuation,
                        # but not cases where there is internal punctuation
                        span_start_strip = span_start + my_word.index(my_word_strip)
                        span_end    = span_start_strip + len(my_word_strip)# + extra
                        '''
                        print '%s, %s, %s goes from %d (%d) to %d' % \
                            (w, my_word, my_word_strip,
                             span_start_strip,
                             my_word.index(my_word_strip),
                             span_end)
                             '''
                    # Format: Tx\tTarget <span_start> <span_end>\t<word>
                        outf.write('T' + str(target_ind) + '\t' +
                                   name + ' ' + str(span_start_strip) + 
                                   ' ' + str(span_end) + '\t' +
                                   my_word_strip + '\n')
                    # Set up for the next target
                        target_ind += 1
                else:
                    span_end    = span_start + len(my_word_strip) + extra
                    
            #print '<%s>, span %d to %d' % (w, span_start, span_end)
            # Either way, update span_start
            span_end   = span_start + len(w)
            span_start = span_end + 1 # Assumes followed by space 
            # (or newline, for final word in line)
        span_start -= 1 # Uncount the newline (double-count)

    # return the latest target_ind for ongoing use
    return target_ind


# Process lines from input file, annotate anything matching 'suffix'
# that is at least min_len in length 
# and does not appear in nonmatches,
# and write out the annotations to outf with type 'name'.
# Number targets starting from start_t.
def pre_annotate_suffix(lines, suffix, min_len, nonmatches, name, outf, start_t):
    # Initialize counters
    target_ind = start_t
    span_start = 0
    span_end = 0

    # Iterate through words and look for a match 
    for l in lines:
        # Specifying ' ' explicitly means that all single spaces
        # will cause a split.  This way we can update span_start
        # correctly even if there are multiple spaces present.
        words = l.split(' ')
        for w in words:
            # Remove any trailing \n etc.
            w_strip = w.strip()
            # Remove any punctuation, except '_', '+' (ions) and '-'
            w_strip = re.sub('[%s]' % re.escape(mypunc), '', w_strip)
            if (w_strip.endswith(suffix) and 
                len(w_strip) >= min_len and
                w_strip not in nonmatches):
                # This handles leading and trailing punctuation,
                # but not cases where there is internal punctuation
                try:
                    span_start_strip = span_start + w.index(w_strip)
                except:
                    # Skip this one
                    print 'Could not handle %s.' % w
                    continue
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

    # return the latest target_ind for ongoing use
    return target_ind


##########################################################

print 'Annotating elements in %d files from %s.' % \
    (len(dirlist), textdir)

# Read in the elements file
with open(elementfile, 'r') as inf:
    lines = inf.readlines()
    elements = [l.strip() for l in lines]
    # Remove ones that are almost always FPs
    elements.remove('As')
    elements.remove('At')
    elements.remove('In')
    elements.remove('Mt')
    elements.remove('No')
    # Add lower-case versions of long element names
    elements += [e.lower() for e in elements if len(e) > 3]

# Read in the minerals file
with open(mineralfile, 'r') as inf:
    lines = inf.readlines()
    minerals = [l.strip() for l in lines]
    # Add lower-case versions
    minerals += [m.lower() for m in minerals]

# Read in the non-minerals file
with open(nonminfile, 'r') as inf:
    lines = inf.readlines()
    nonminerals = [l.strip() for l in lines]
    # Add lower-case versions
    nonminerals += [m.lower() for m in nonminerals]
    
# Read in the Chemcam targets file
with open(chemcamfile, 'r') as inf:
    lines = inf.readlines()
    chemcam_targets = [l.strip() for l in lines]
    # Add a version with space converted to _
    chemcam_targets += [re.sub(' ', '_', cc) for cc in chemcam_targets \
                            if ' ' in cc]
    # Add a version with trailing _CCAM or _ccam removed
    chemcam_targets += [cc[:-5] for cc in chemcam_targets \
                            if cc.endswith('_CCAM') or cc.endswith('_ccam')]
    # Add a version with trailing _DRT or _drt removed
    chemcam_targets += [cc[:-4] for cc in chemcam_targets \
                             if cc.endswith('_DRT') or cc.endswith('_drt')]
    # Add a version with trailing _1 or _2 removed
    chemcam_targets += [cc[:-2] for cc in chemcam_targets \
                             if cc.endswith('_1') or cc.endswith('_2')] 
    # Add a version with _ converted to space
    chemcam_targets += [re.sub('_', ' ', cc) for cc in chemcam_targets \
                            if '_' in cc]
    
print 'Read in %d ChemCam target names.' % len(chemcam_targets)

'''
# Read in the MER targets file
with open(MERfile, 'r') as inf:
    lines = inf.readlines()
    mer_targets = [l.strip() for l in lines]
    # Add a version with _ converted to space
    mer_targets_a = [re.sub('_', ' ', cc) for cc in mer_targets \
                         if '_' in cc]
    # Add a version with space converted to _
    mer_targets_b = [re.sub(' ', '_', cc) for cc in mer_targets \
                             if ' ' in cc]
    mer_targets += mer_targets_a
    mer_targets += mer_targets_b

print 'Read in %d MER target names.' % len(mer_targets)
'''

# Iterate through documents; output to .ann file
for fn in dirlist:
    print fn

    # Read in the input .txt document
    with open(textdir + '/' + fn, 'r') as inf:
        lines = inf.readlines()

    annfile = textdir + '/' + fn[0:-4] + '.ann'

    # Create the annotations
    start_t = 1
    with open(annfile, 'w') as outf:
        start_t = pre_annotate(lines, elements,        'Element', outf, start_t)
        start_t = pre_annotate(lines, chemcam_targets, 'Target',  outf, start_t)
#        start_t = pre_annotate(lines, mer_targets,     'Target',  outf, start_t)
        start_t = pre_annotate_suffix(lines, 'ite', 6, nonminerals, 'Mineral', outf, start_t)
        start_t = pre_annotate(lines, minerals,        'Mineral', outf, start_t)
#        sys.exit(0)


    

