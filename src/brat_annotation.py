# brat_annotation.py
# Helper methods for parsing and manipulating brat annotations.
# Strongly inspired by 
# https://github.com/ryanaustincarlson/moocdb/blob/master/annotate/BratAnnotation.py
#
# Kiri Wagstaff
# January 12, 2016

import sys, os
import dbutils


class BratAnnotation:
    def __init__(self, annotation_line, doc_id, username):
        self.doc_id   = doc_id
        self.username = username

        #annotation_id, markup, name = annotation_line.strip().split('\t')
        splitline = annotation_line.strip().split('\t')
        self.annotation_id = splitline[0]

        if splitline[0][0] == 'T': # target
            self.label   = splitline[1].split()[0]
            args         = splitline[1].split()[1:]
            self.start   = args[0]
            self.end     = args[-1]
            self.name    = splitline[2]
        elif splitline[0][0] == 'E': # event
            args = splitline[1].split() 
            self.label   = args[0].split(':')[0]
            args         = [a.split(':') for a in args[1:]]
            self.targets = [v for (t,v) in args if t.startswith('Targ')]
            self.cont    = [v for (t,v) in args if t.startswith('Cont')]
        elif splitline[0][0] == 'R': # relation
            label, arg1, arg2 = splitline[1].split() # assumes 2 args
            self.label   = label
            self.arg1    = arg1.split(':')[1]
            self.arg2    = arg2.split(':')[1]
        elif splitline[0][0] == 'A': # attribute
            label, arg, value = splitline[1].split()
            self.label   = label
            self.arg1    = arg
            self.value   = value
        else:
            print 'Unknown annotation type:', splitline[0]


    def insert(self, cursor):

        # Insert into the appropriate table depending on the annotation type
        if self.label == 'Target':
            dbutils.insert_into_table(
                cursor=cursor,
                table='targets',
                columns=['target_id', 'target_name'],
                values=[self.doc_id+'_'+self.annotation_id, self.name])
        elif (self.label == 'Element' or 
              self.label == 'Mineral' or 
              self.label == 'Material' or 
              self.label == 'Feature'):
            dbutils.insert_into_table(
                cursor=cursor,
                table='components',
                columns=['component_id', 'component_name', 'component_label'],
                values=[self.doc_id+'_'+self.annotation_id, 
                        self.name, 
                        self.label])
        elif self.label == 'Contains':
            # If it's just 'Contains' with no arguments, then self.targets
            # doesn't exist and this annotation is just the anchor word;
            # ignore for now
            try:
                # Loop over all targets
                for t in self.targets:
                    # Loop over all constituents
                    for v in self.cont:
                        dbutils.insert_into_table(
                            cursor=cursor,
                            table='contains',
                            columns=['event_id',  'doc_id', 
                                     'target_id', 'component_id', 
                                     'magnitude', 'confidence',   'annotator'],
                            values=[self.doc_id+'_'+self.annotation_id, 
                                    self.doc_id,
                                    self.doc_id+'_'+t,
                                    self.doc_id+'_'+v,
                                    'unknown',
                                    'neutral',
                                    self.username])
            except: 
                pass
        elif self.label == 'Contains_low':
            dbutils.insert_into_table(
                cursor=cursor,
                table='contains',
                columns=['target_id','component_id','doc_id','magnitude','confidence','annotator'],
                values=[self.doc_id+'_'+self.arg1,
                        self.doc_id+'_'+self.arg2,
                        self.doc_id,
                        'low',
                        'neutral',
                        self.username])
        elif self.label == 'Contains_high':
            dbutils.insert_into_table(
                cursor=cursor,
                table='contains',
                columns=['target_id','component_id','doc_id','magnitude','confidence','annotator'],
                values=[self.doc_id+'_'+self.arg1,
                        self.doc_id+'_'+self.arg2,
                        self.doc_id,
                        'high',
                        'neutral',
                        self.username])
        elif self.label == 'May_contain':
            dbutils.insert_into_table(
                cursor=cursor,
                table='contains',
                columns=['target_id','component_id','doc_id','magnitude','confidence','annotator'],
                values=[self.doc_id+'_'+self.arg1,
                        self.doc_id+'_'+self.arg2,
                        self.doc_id,
                        'unknown',
                        'low',
                        self.username])
        elif self.label == 'Lacks':
            dbutils.insert_into_table(
                cursor=cursor,
                table='contains',
                columns=['target_id','component_id','doc_id','magnitude','confidence','annotator'],
                values=[self.doc_id+'_'+self.arg1,
                        self.doc_id+'_'+self.arg2,
                        self.doc_id,
                        'none',
                        'neutral',
                        self.username])
        elif (self.label == 'Locality' or
              self.label == 'Formation' or 
              self.label == 'IsSituatedIn' or
              self.label == 'Shows' or
              self.label == 'Material' or
              self.label == 'DoesNotShow' or
              self.label == 'Confidence' or
              self.label == 'Site' or
              self.label == 'StratRel' or
              self.label == 'Position' or 
              self.label == 'Amount' or
              self.label == 'Region'):
            # Not yet handled
            pass
        else:
            raise RuntimeError('Unknown label %s' % self.label)

