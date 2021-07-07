# python2
# This code checks the statistics through ann files

# command line:
#   python2 check_annotation_stats.py <dir-that-contains-lpsc15-ann-files> <dir-that-contains-lpsc16-ann-files>

# Sample command line: 
#   python2 check_annotation_stats.py /home/yzhuang/mte/data/corpus-LPSC/lpsc15-C-raymond-sol1159-v3-utf8 /home/yzhuang/mte/data/corpus-LPSC/lpsc16-C-raymond-sol1159-utf8


import sys, os, re, string, glob
from os.path import dirname, join
import itertools

# BratAnnotation is copied from the file https://github.com/wkiri/MTE/blob/master/src/brat_annotation.py. Nothing is changed except one function count() is added to check the stats. 
class BratAnnotation:
    def __init__(self, annotation_line, doc_id, username):
        self.doc_id   = doc_id
        self.username = username

        #annotation_id, markup, name = annotation_line.strip().split('\t')
        splitline = annotation_line.strip().split('\t')
        self.annotation_id = splitline[0]

        if splitline[0][0] == 'T': # anchors (for targets, components, events)
            self.type    = 'anchor'
            self.label   = splitline[1].split()[0]
            args         = splitline[1].split()[1:]
            self.start   = args[0]
            self.end     = args[-1]
            self.name    = splitline[2]
        elif splitline[0][0] == 'E': # event
            self.type    = 'event'
            args         = splitline[1].split() 
            self.label   = args[0].split(':')[0]
            self.anchor  = args[0].split(':')[1]
            args         = [a.split(':') for a in args[1:]]
            self.targets = [v for (t,v) in args if t.startswith('Targ')]
            self.cont    = [v for (t,v) in args if t.startswith('Cont')]
        elif splitline[0][0] == 'R': # relation
            self.type    = 'relation'
            label, arg1, arg2 = splitline[1].split() # assumes 2 args
            self.label   = label
            self.arg1    = arg1.split(':')[1]
            self.arg2    = arg2.split(':')[1]
        elif splitline[0][0] == 'A': # attribute
            self.type    = 'attribute'
            label, arg, value = splitline[1].split()
            self.label   = label
            self.arg1    = arg
            self.value   = value
        else:
            print 'Unknown annotation type:', splitline[0]

    # added function to check the stats by counting the number of targets, elements, minerals and contains relations.
    def count(self):
        self.num_target = 0
        self.num_element = 0
        self.num_mineral = 0
        self.num_contains = 0
        if self.type == 'anchor':
            if self.label == 'Target':
                self.num_target = 1
            elif self.label == 'Element':
                self.num_element = 1
            elif self.label == 'Mineral':
                self.num_mineral = 1
        if self.type == 'relation':
            if self.label == 'Target':
                self.num_target = 1
            elif self.label == 'Element':
                self.num_element = 1
            elif self.label == 'Mineral':
                self.num_mineral = 1
        elif self.type == 'event' and self.label == 'Contains':
            for t in self.targets:
                for v in self.cont:
                    self.num_contains += 1


def count(dir, dataset_name):
    num_target = 0
    num_element = 0 
    num_mineral = 0
    num_contains = 0
    num_files = 0
    for ann_file in glob.glob(join(dir, "*.ann")):
        num_files += 1
        with open(ann_file,"r") as f:
            lines = f.read().strip().split("\n")
        for line in lines:
            line = line.strip()
            if line == "": continue
            brat = BratAnnotation(line, "", "")
            brat.count()
            num_target += brat.num_target
            num_element += brat.num_element
            num_mineral += brat.num_mineral
            num_contains += brat.num_contains
    print("In %s, there are %d files, %d targets, %d elements, %d minerals, %d contains relations" % (dataset_name, num_files, num_target, num_element, num_mineral, num_contains))


def main(args):
    lpsc15_dir, lpsc16_dir, phx_dir, mpf_dir = args

    count(lpsc15_dir, "LPSC15")
    count(lpsc16_dir, "LPSC16")
    count(phx_dir, "PHX")
    count(mpf_dir, "MPF")


if __name__ == "__main__":
    args = (sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
    main(args)


