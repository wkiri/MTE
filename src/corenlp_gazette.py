#!/usr/bin/env/ python
# -*- coding: utf-8 -*-
#
# Read a list, and convert it to CoreNLP gazette format.
# 1. If a name in input list contains "_", duplicate the name in the 
# CoreNLP gazette list, then replace "_" with space. 
# 2. If a name in input list contains accented character, duplicate 
# the name in the CoreNLP gazette list, then normalize the accented
# character to its corresponding ascii representation.
# 3. If a name in input list contains "?", remove it from the CoreNLP
# gazette list.
# 4. If a name is a Mineral, and it is in 'mineral_remove_list', it 
# will be removed from the CoreNLP gazette list.
#
# Example input format:
#     Adams_Sound
#     Abbabis
#     Achávalite
#     Bali??uni?ite
#     ...
#     Afton_Cayon_CCAM
# 
# Example output CoreNLP gazette format:
#     Target Adams_Sound
#     Target Adams Sound
#     Target Abbabis
#     Mineral Achávalite
#     Mineral Achavalite
#     ...
#     Target Afton_Cayon_CCAM
#     Target Afton Cayon CCAM
#
# Author: Steven Lu
# August 4, 2017
# Copyright notice at bottom of file.

import os, sys
import unidecode

# The follow items appear in both mineral and element list.
# We keep them in element list, but remove them in mineral list
# to avoid confusion.
mineral_remove_list = [
    'Aluminium',
    'Antimony',
    'Arsenic', 
    'Bismuth',
    'Cadmium',
    'Cerium',
    'Chromium',
    'Copper',
    'Gold',
    'Indium',
    'Iridium',
    'Iron',
    'Lead',
    'Mercury',
    'Nickel',
    'Osmium',
    'Palladium',
    'Platinum',
    'Rhodium',
    'Ruthenium',
    'Selenium',
    'Silicon',
    'Silver',
    'Tellurium',
    'Tin', 
    'Titanium',
    'Tungsten',
    'Vanadium',
    'Zinc'
]

def main(in_list, out_list, class_type):
    # verify in_list exist
    if not os.path.isfile(in_list):
        print 'input list %s does not exist.' % in_list
        sys.exit()

    with open(in_list, 'r') as il:
        il_content = il.readlines()
    
    remove_counter = 0
    underscore_counter = 0
    accented_counter = 0
    ques_mark_counter = 0 # question mark counter
    il_content = [x.strip() for x in il_content]
    with open(out_list, 'w') as ol:
        for name in il_content:
            if class_type == 'Mineral' and any(name in mn for mn in mineral_remove_list):
                remove_counter += 1
                continue
 
            if '?' in name:
                ques_mark_counter += 1
                continue
    
            name_utf8 = unicode(name, 'utf8')

            gaz_name = '%s %s\n' % (class_type, name)
            ol.write(gaz_name)

            if not name == name_utf8:
                name_utf8 = unidecode.unidecode(name_utf8)
                gaz_name_utf8 = '%s %s\n' % (class_type, name_utf8)
                ol.write(gaz_name_utf8)
                accented_counter += 1

            if '_' in gaz_name:
                gaz_name = gaz_name.replace('_', ' ')
                ol.write(gaz_name)
                underscore_counter += 1

    in_num = len(il_content)
    out_num = sum(1 for line in open(out_list))
    print 'Total number of input: %d' % in_num
    print 'Total number of input in mineral remove list: %d' % remove_counter
    print 'Total number of input contains question mark: %d' % ques_mark_counter
    print 'Total number of input contains underscore: %d' % underscore_counter
    print 'Total number of input contains accented characters: %d' % accented_counter
    print 'Total number of output: %d' % out_num 
    
    # consistency check
    if in_num + underscore_counter + accented_counter - remove_counter - ques_mark_counter == out_num:
        print 'Consistency check done.'
    else:
        print 'Consistency check failed.'

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('in_list', help='Input list, one name per row.')
    parser.add_argument('out_list', help='Output list in CoreNLP gazette format')
    parser.add_argument('class_type', help='Class type. Valid options are Target, Element, Mineral')
    args = parser.parse_args()
    main(args.in_list, args.out_list, args.class_type)

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
