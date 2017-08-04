#!/usr/bin/env/ python
#
# Read a list, and convert it to CoreNLP gazette format.
# If a name in input list contains "_", duplicate the name in the 
# CoreNLP gazette list, then replace "_" with space. 
#
# Example input format:
#     Adams_Sound
#     Abbabis
#     ...
#     Afton_Cayon_CCAM
# 
# Example output CoreNLP gazette format:
#     Target Adams_Sound
#     Target Adams Sound
#     Target Abbabis
#     ...
#     Target Afton_Cayon_CCAM
#     Target Afton Cayon CCAM
#
# Author: Steven Lu
# August 4, 2017

import os, sys

def main(in_list, out_list, class_type):
    # verify in_list exist
    if not os.path.isfile(in_list):
        print 'input list %s does not exist.' % in_list
        sys.exit()

    with open(in_list, 'r') as il:
        il_content = il.readlines()
    
    underscore_counter = 0
    il_content = [x.strip() for x in il_content]
    with open(out_list, 'w') as ol:
        for name in il_content:
            # remove non-ascii characters
            name = ''.join((ch for ch in name if 0 < ord(ch) < 127)) 

            gaz_name = '%s %s\n' % (class_type, name)
            ol.write(gaz_name)

            if '_' in gaz_name:
                gaz_name = gaz_name.replace('_', ' ')
                ol.write(gaz_name)
                underscore_counter += 1

    in_num = len(il_content)
    out_num = sum(1 for line in open(out_list))
    print 'Total number of input: %d' % in_num
    print 'Total number of input contains underscore: %d' % underscore_counter
    print 'Total number of output: %d' % out_num 
    
    # consistency check
    if in_num + underscore_counter == out_num:
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
