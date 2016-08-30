# brat_annotation.py
# Helper methods for parsing and manipulating brat annotations.
# Strongly inspired by 
# https://github.com/ryanaustincarlson/moocdb/blob/master/annotate/BratAnnotation.py
#
# Kiri Wagstaff
# January 12, 2016

import sys, os
import dbutils

# Map annotation labels to database table names and columns
lookups = {'Target':   ('targets', 'target_name'),   
           'Element':  ('components', 'component_name'),
           'Mineral':  ('components', 'component_name'),
           'Material': ('components', 'component_name'),
           'Feature':  ('components', 'component_name')}


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
            self.targets = [v for (t,v) in args if t == 'Targ']
            self.cont    = [v for (t,v) in args if t == 'Cont']
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

    def insert(self, cursor):

        # Insert into the appropriate table depending on the annotation type

        # Basic annotations (type T in .ann files) are inserted into
        # the anchors table, which tracks all text mentions (and spans).
        if self.type == 'anchor':
            canonical = ''

            # Targets and components:
            # Look up canonical entry, or add if needed.
            if self.label in lookups.keys():
                # Canonical name in all lower case
                canonical = self.name.lower()
                (tabname, colname) = lookups[self.label]
                cursor.execute("SELECT %s FROM %s " % (colname, tabname) +
                               "WHERE %s ILIKE '%s';" % (colname, self.name))
                name = cursor.fetchone()
                if name == None:
                    # Add the label for components
                    if tabname == 'components':
                        dbutils.insert_into_table(
                            cursor=cursor,
                            table=tabname,
                            columns=[colname, 'component_label'],
                            values=[canonical, self.label])
                    else: # Just add the name
                        dbutils.insert_into_table(
                            cursor=cursor,
                            table=tabname,
                            columns=[colname],
                            values=[canonical])

            # Add this anchor.  Text other than targets and components
            # will not have a canonical entry.  That's okay.
            dbutils.insert_into_table(
                cursor=cursor,
                table='anchors',
                columns=['anchor_id', 'label', 
                         'canonical', 'text',
                         'span_start', 'span_end'],
                values=[self.doc_id+'_'+self.annotation_id, self.label,
                        canonical,  self.name,
                        self.start, self.end])

        # Events are 
        elif self.type == 'event':
            if self.label == 'Contains':
                print self.anchor
                # Loop over all targets
                for t in self.targets:
                    # Loop over all constituents
                    for v in self.cont:
                        # Extract the excerpt 
                        cursor.execute("SELECT content " +
                                       "FROM documents " +
                                       "WHERE doc_id='%s';" \
                                           % (self.doc_id))
                        content = cursor.fetchone()
                        if content == None:
                            print 'Warning: document %s not found, skipping.' % \
                                self.doc_id
                            break

                        # Compute the likely start and end of the sentence
                        content = content[0]
                        cursor.execute("SELECT span_start, span_end " +
                                       "FROM anchors " +
                                       "WHERE anchor_id='%s';" \
                                           % (self.doc_id+'_'+self.anchor))
                        (anchor_start,anchor_end) = cursor.fetchone()
                        sent_start = max(content[:anchor_start].rfind('.'),0)+1
                        sent_end   = anchor_end + \
                            min(content[anchor_end:].find('.'),len(content))+1
                        excerpt = content[sent_start:sent_end]

                        # Get the canonical forms of the target and component
                        cursor.execute("SELECT canonical " +
                                       "FROM anchors " +
                                       "WHERE anchor_id='%s';" \
                                           % (self.doc_id+'_'+t))
                        canonical_t = cursor.fetchone()[0]
                        cursor.execute("SELECT canonical " +
                                       "FROM anchors " +
                                       "WHERE anchor_id='%s';" \
                                           % (self.doc_id+'_'+v))
                        canonical_v = cursor.fetchone()[0]

                        # Insert into table
                        dbutils.insert_into_table(
                            cursor=cursor,
                            table='contains',
                            columns=['event_id',  'doc_id', 'anchor_id',
                                     'target_name', 'component_name', 
                                     'magnitude', 'confidence',   
                                     'annotator', 'excerpt'],
                            values=[self.doc_id+'_'+self.annotation_id, 
                                    self.doc_id,
                                    self.doc_id+'_'+self.anchor,
                                    canonical_t, canonical_v,
                                    'unknown',
                                    'neutral',
                                    self.username,
                                    excerpt])
            elif (self.label == 'DoesNotContain' or
                  self.label == 'StratRel'):
                # Not yet handled
                pass

        elif self.type == 'relation':
            # Not yet handled
            pass
        elif self.type == 'attribute':
            # Not yet handled
            pass
        else:
            raise RuntimeError('Unknown label %s' % self.label)

