# brat_annotation_sqlite.py
# Helper methods for parsing and manipulating brat annotations with respect to
# the MTE sqlite DB schema (See the link below).
#
# https://github-fn.jpl.nasa.gov/wkiri/mte/wiki/MTE-SQLite-Database-Schema
#
# Steven Lu
# November 4, 2020

import os
import json
from name_utils import canonical_name, standardize_target_name, \
    canonical_property_name


TYPE_ENTITY = 'entity'
TYPE_RELATION = 'relation'
TYPE_EVENT = 'event'
TYPE_NOT_SUPPORTED = 'not_yet_supported'
SUPPORTED_LABELS = ['Target', 'Element', 'Mineral', 'Property', 'Contains',
                    'HasProperty']


class BratDocument(object):
    def __init__(self, ann_path, txt_path, doc_id='', mission='', reviewer='',
                 canonical_mapping=True):
        self.ann_path = ann_path
        self.txt_path = txt_path
        self.doc_id = doc_id
        self.mission = mission
        self.reviewer = reviewer
        self.canonical_mapping = canonical_mapping
        self.ann_content = self.read_ann_content()
        self.txt_content = self.read_txt_content()

    # Read Brat ann file and return a list of BratAnnotation
    def read_ann_content(self):
        if not os.path.exists(self.ann_path):
            raise RuntimeError('ann file not found: %s' %
                               os.path.abspath(self.ann_path))

        with open(self.ann_path, 'r') as f:
            ann_lines = f.readlines()

        ann_content = []
        for ann_line in ann_lines:
            # Skip blank lines
            if len(ann_line.strip()) == 0:
                continue

            brat_ann = BratAnnotation(ann_line, self.canonical_mapping)
            if brat_ann.label not in SUPPORTED_LABELS:
                continue

            ann_content.append(brat_ann)

        return ann_content

    # Read Brat txt file and return the content of the file as a string
    def read_txt_content(self):
        if not os.path.exists(self.txt_path):
            raise RuntimeError('txt file not found: %s' %
                               os.path.abspath(self.txt_path))
        with open(self.txt_path, 'r') as f:
            file_content = f.readlines()

        if len(file_content) != 1:
            raise RuntimeError('Invalid txt file format: %s' %
                               os.path.abspath(self.txt_path))

        return file_content[0].decode('utf8')
        # return file_content[0]


class BratAnnotation:
    def __init__(self, brat_line, canonical_mapping=True):
        record = self.parse_brat_line(brat_line, canonical_mapping)
        self.ann_id = record['ann_id']
        self.type = record['type']
        self.label = record['label']
        if self.type == TYPE_ENTITY:
            # Only used by entities
            self.start = record['start']
            self.end = record['end']
            self.name = record['name']
        elif self.type == TYPE_RELATION:
            # Only used by relations
            self.arg1 = record['arg1']
            self.arg2 = record['arg2']
        elif self.type == TYPE_EVENT:
            # Only used by events
            self.targs = record['targs']
            self.conts = record['conts']

    def __str__(self):
        ret = self.label + ' (%s)' % self.ann_id
        if self.type == TYPE_ENTITY:
            ret += ': %s (%s - %s)' % (self.name, self.start, self.end)
        elif self.type == TYPE_RELATION:
            ret += ': %s -> %s' % (self.arg1, self.arg2)
        elif self.type == TYPE_EVENT:
            ret += ': %s -> %s' % (json.dumps(self.targs),
                                   json.dumps(self.conts))
        return ret

    @staticmethod
    def parse_brat_line(brat_line, canonical_mapping):
        line_tokens = brat_line.strip().split('\t')
        middle_tokens = line_tokens[1].split()

        if line_tokens[0][0] == 'T':
            ann_type = TYPE_ENTITY
            ann_label = middle_tokens[0]
        elif line_tokens[0][0] == 'R':
            ann_type = TYPE_RELATION
            ann_label = middle_tokens[0]
        elif line_tokens[0][0] == 'E':
            ann_type = TYPE_EVENT
            ann_label = middle_tokens[0].split(':')[0]
        else:
            ann_type = TYPE_NOT_SUPPORTED
            ann_label = middle_tokens[0]

        # Add generic attribution attributes
        record = {
            'ann_id': line_tokens[0],
            'type': ann_type,
            'label': ann_label
        }

        # Add type-specific attributes
        if ann_type == TYPE_ENTITY:
            record['start'] = int(middle_tokens[1])
            record['end'] = int(middle_tokens[2])
            nm = line_tokens[2].decode('utf-8')
            # Use lower-case for properties
            if canonical_mapping:
                if record['label'] == 'Property':
                    record['name'] = canonical_property_name(nm)
                elif record['label'] == 'Target':
                    record['name'] = standardize_target_name(nm)
                else:
                    record['name'] = canonical_name(nm)
            else:
                record['name'] = nm
        elif ann_type == TYPE_RELATION:
            # These arguments are of the form ArgN:TXX
            record['arg1'] = middle_tokens[1].split(':')[1]
            record['arg2'] = middle_tokens[2].split(':')[1]
        elif ann_type == TYPE_EVENT:
            conts = []
            targs = []
            for inner_token in middle_tokens[1:]:
                t1, t2 = inner_token.split(':')
                if 'Cont' in t1:
                    conts.append(t2)
                elif 'Targ' in t1:
                    targs.append(t2)

            record['conts'] = conts
            record['targs'] = targs

        return record

