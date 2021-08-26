#!/usr/bin/env python
# pre_annotate.py
# Annotate target names and elements in .txt files;
# write them out in brat .ann form.
#
# Kiri Wagstaff
# February 18, 2016
# Copyright notice at bottom of file.

import sys, os, io
import string
import re

# Remove any punctuation, except '_' and '+' (ions) and '-' 
# and '.' (e.g., Mt. Sharp)
mypunc = string.punctuation
for p in ['_', '\+', '-', '\.']:
    mypunc = re.sub(p, '', mypunc)

# Process text from input file, annotate anything that matches 'items',
# and write out the annotations to outf with type 'name'.
# Number targets starting from start_t.
def pre_annotate(chars, items, name, outf, start_t):
    # Initialize counters
    target_ind = start_t
    span_start = 0
    span_end = 0

    # Specifying ' ' explicitly means that all single spaces
    # will cause a split.  This way we can update span_start
    # correctly even if there are multiple spaces present.
    words = chars.split(' ')  # Already Unicode
    for (i,w) in enumerate(words):
        # This check slows us down, but ensures we didn't mess up the indexing!
        if w != chars[span_start:span_start+len(w)]:
            print 'Error: <%s> and <%s> do not match.' % (w,
                                                          chars[span_start:span_start+len(w)])
            raw_input()
                
        end_of_sentence = False

        # Remove any trailing \n etc.
        w_strip = w.strip()
        #print '<%s>,<%s>' % (w,w_strip)
        # Track whether this is a potential end of sentence
        # to avoid spurious element abbreviation annotations
        if w_strip.endswith('.'):
            end_of_sentence = True
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
            extra = 0 # Characters we stripped off but still need to count in spans
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
                    try:
                        span_start_strip = span_start + my_word.index(my_word_strip)
                    except: # internal punctuation, so skip it 
                        # (fine as long as ONE of these succeeds...
                        # otherwise span_start needs an update)
                        print 'Skipping', my_word, my_word_strip
                        continue
                    span_end    = span_start_strip + len(my_word_strip)# + extra
                    '''
                    print '%s, %s, %s goes from %d (%d) to %d' % \
                    (w, my_word, my_word_strip,
                    span_start_strip,
                    my_word.index(my_word_strip),
                    span_end)
                    raw_input()
                    '''
                    # Check that annotation and offsets match
                    if chars[span_start_strip:span_end] != my_word_strip:
                        print 'Error: <%s> and <%s> do not match.' % (my_word_strip,
                                                                          chars[span_start_strip:span_end])
                        raw_input()

                    # Format: Tx\tTarget <span_start> <span_end>\t<word>
                    outf.write('T' + str(target_ind) + '\t' +
                               name + ' ' + str(span_start_strip) + 
                               ' ' + str(span_end) + '\t' +
                               my_word_strip + '\n')
                    # Set up for the next target
                    target_ind += 1
            else:
                span_end    = span_start + len(my_word_strip) + extra
                    
            #print '<%s>, <%s>, span %d to %d' % (w, my_word, span_start, span_end)

        # Either way, update span_start
        span_end   = span_start + len(w)
        #span_start = span_end
        span_start = span_end + 1 # Assumes followed by space 

    # return the latest target_ind for ongoing use
    return target_ind


# Process text from input file, annotate anything matching 'suffix'
# that is at least min_len in length 
# and does not appear in nonmatches,
# and write out the annotations to outf with type 'name'.
# Number targets starting from start_t.
def pre_annotate_suffix(chars, suffix, min_len, nonmatches, name, outf, start_t):
    # Initialize counters
    target_ind = start_t
    span_start = 0
    span_end = 0

    # Specifying ' ' explicitly means that all single spaces
    # will cause a split.  This way we can update span_start
    # correctly even if there are multiple spaces present.
    words = chars.split(' ')  # Already Unicode

    for w in words:
        # This check slows us down, but ensures we didn't mess up the indexing!
        if w != chars[span_start:span_start+len(w)]:
            print 'Error: <%s> and <%s> do not match.' % (w,
                                                          chars[span_start:span_start+len(w)])
            raw_input()
                
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
                span_start += (len(w) + 1)
                continue
            span_end    = span_start_strip + len(w_strip) 

            # Check that annotation and offsets match
            if chars[span_start_strip:span_end] != w_strip:
                print 'Error: <%s> and <%s> do not match.' % (w_strip,
                                                              chars[span_start_strip:span_end])
                raw_input()

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

    # return the latest target_ind for ongoing use
    return target_ind


##########################################################
def main(textdir, anndir, elementfile, mineralfile, IMAmineralfile,
         propertyfile, targetfile):

    # Check arguments
    for f in [elementfile, mineralfile, IMAmineralfile,
              propertyfile, targetfile]:
        if not os.path.exists(f):
            print('Could not read %s' % f)
            sys.exit(1)

    if not os.path.isdir(textdir):
        print('Could not find text directory %s' % textdir)
        sys.exit(1)

    if not os.path.isdir(anndir):
        s = raw_input('Output directory %s does not exist; create it? [Y/n]'
                      % anndir)
        if s in ['n', 'N']:
            print('Exiting.')
            sys.exit(1)
        else:
            os.mkdir(anndir)

    # Files to analyze
    dirlist = [fn for fn in os.listdir(textdir) if
               fn.endswith('.txt')]

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
        minerals += [l.strip().lower() for l in lines]

    # Read in the IMA minerals file
    with open(IMAmineralfile, 'r') as inf:
        lines = inf.readlines()
        minerals += [l.strip() for l in lines]
        # Add lower-case versions
        minerals += [l.strip().lower() for l in lines]

    # Remove duplicates
    minerals = list(set(minerals))

    # Read in the properties file
    with open(propertyfile, 'r') as inf:
        lines = inf.readlines()
        properties = [l.strip() for l in lines]
        # Add lower-case versions
        properties += [l.strip().lower() for l in lines]
        # Add upper-case versions
        properties += [l.strip().upper() for l in lines]
        # Add title-case versions
        properties += [l.strip().title() for l in lines]
        
    # Remove duplicates
    properties = list(set(properties))

    # Read in the targets file
    with open(targetfile, 'r') as inf:
        lines = inf.readlines()
        targets = [l.strip() for l in lines]
        # Add a version with space converted to _
        targets += [re.sub(' ', '_', cc) for cc in targets \
                            if ' ' in cc]
        # Chemcam-specific processing:
        # Add a version with trailing _CCAM or _ccam removed
        targets += [cc[:-5] for cc in targets \
                            if cc.endswith('_CCAM') or cc.endswith('_ccam')]
        # Add a version with trailing _DRT or _drt removed
        targets += [cc[:-4] for cc in targets \
                            if cc.endswith('_DRT') or cc.endswith('_drt')]
        # Add a version with trailing _RMI or _RMI removed
        targets += [cc[:-4] for cc in targets \
                            if cc.endswith('_RMI') or cc.endswith('_rmi')]
        # Add a version with trailing _1 or _2 removed
        targets += [cc[:-2] for cc in targets \
                            if cc.endswith('_1') or cc.endswith('_2')] 
        # Add a version with _ converted to space
        targets += [re.sub('_', ' ', cc) for cc in targets \
                            if '_' in cc]

    # Get rid of duplicates
    t = len(targets)
    targets = list(set(targets))
    print 'Read in %d -> %d target names.' % (t, len(targets))

    # Iterate through documents; output to .ann file
    for fn in dirlist:
        # Restrict which files to process
        #if int(fn.split('.')[0].split('_')[0]) > 1999:
        #    sys.exit(0)
        print fn

        # Read in all of the characters so we can track offsets
        with open(textdir + '/' + fn, 'r') as inf:
            # Convert UTF-8 to a Unicode string, so funky chars don't get counted
            # as two bytes instead of one.
            chars = inf.read().decode('utf8')
            inf.close()

        #annfile = textdir + '/' + fn[0:-4] + '.ann'
        annfile = os.path.join(anndir, fn[0:-4] + '.ann')

        # Create the annotations
        start_t = 1
        # Append to any existing annotations
        if os.path.exists(annfile):
            # Get the current max so ids can start after that
            max_target_id = 0
            with io.open(annfile, 'r', encoding='utf8') as inf:
                for l in inf:
                    if l.startswith('T'):
                        id = int(l.split('\t')[0][1:])
                        if id > max_target_id:
                            max_target_id = id
            start_t = max_target_id + 1

        with io.open(annfile, 'a', encoding='utf8') as outf:
            #start_t = pre_annotate(chars, elements, 'Element', outf, start_t)
            start_t = pre_annotate(chars, targets,  'Target',  outf, start_t)
            #start_t = pre_annotate(chars, properties,  'Property',  outf, start_t)
            #        start_t = pre_annotate(chars, mer_targets,     'Target',  outf, start_t)
            #        start_t = pre_annotate_suffix(chars, 'ite', 6, nonminerals, 'Mineral', outf, start_t)
            #start_t = pre_annotate(chars, minerals, 'Mineral', outf, start_t)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(argument_default=argparse.SUPPRESS, description='Apply known target, element, mineral, and property types to LPSC documents')

    parser.add_argument('textdir', 
                        help='Location of input .txt files (UTF-8)')
    parser.add_argument('anndir', 
                        help='Where to write output .ann files')
    parser.add_argument('-e', '--elementfile', default='../ref/element-correct-MPF+periodic-table.txt',
                        help='List of known element names')
    parser.add_argument('-m', '--mineralfile', default='../ref/mineral-correct-MPF+IMA.gaz.txt',
                        help='List of known mineral names')
    parser.add_argument('-i', '--IMAmineralfile', 
                        default='../ref/minerals-IMA-2017-05.txt',
                        help='List of known mineral names from the IMA')
    parser.add_argument('-p', '--propertyfile', default='../ref/properties.txt',
                        help='List of known properties')
    parser.add_argument('-t', '--targetfile', 
                        default='../ref/MSL/chemcam-targets-sol1159.txt',
                        help='List of mission-specific target names')

    args = parser.parse_args()
    main(**vars(args))


# Copyright 2016, by the California Institute of Technology. ALL
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
