import sys, os, re, string, glob
from os.path import join
# import dbutils
import itertools


class BratAnnotation:
    # def __init__(self, annotation_line, doc_id, username):
    def __init__(self, annotation_line):
        # self.doc_id   = doc_id
        # self.username = username

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
            print('Unknown annotation type:', splitline[0])


    def insert(self):
   
        self.relations = []
        if self.type == 'event':
            if self.label == 'Contains':
                # Loop over all targets
                for t in self.targets:
                    # Loop over all constituents
                    for v in self.cont:
                        #MODIFIED
                        self.relations.append((t,v))


        


"""
modify the directory of ann files here
"""

INPUT_DIR = "../../../data/corpus-LPSC/lpsc15" # e.g. PATH/TO/lpsc15 or lpsc16

""" 
end moficiation 
"""

annfiles = glob.glob(join(INPUT_DIR, "*.ann"))
print("collected {} files from {}".format(len(annfiles), INPUT_DIR))
contain_relations = []
for file in annfiles:
    # collect lines from file 
    lines = [line for line in open(file, "r").readlines() if line.strip() != ""]
    for line in lines:
        brat = BratAnnotation(line)
        brat.insert() # make self.relations
        contain_relations.extend(brat.relations)
print("collected {} contain-relations (including relations between all NERs)".format(len(contain_relations)))



lookups = {'Target':   ('targets', 'target_name'),   
           'Element':  ('components', 'component_name'),
           'Mineral':  ('components', 'component_name'),
           'Material': ('components', 'component_name'),
           'Feature':  ('components', 'component_name')}
