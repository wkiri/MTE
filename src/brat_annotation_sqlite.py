# brat_annotation_sqlite.py
# Helper methods for parsing and manipulating brat annotations with respect to
# the MTE sqlite DB schema (See the link below).
#
# https://github-fn.jpl.nasa.gov/wkiri/mte/wiki/MTE-SQLite-Database-Schema
#
# Steven Lu
# November 4, 2020

import os
from name_utils import canonical_name


TYPE_ENTITY = 'entity'
TYPE_RELATION = 'relation'
SUPPORTED_LABELS = ['Target', 'Element', 'Mineral', 'Property', 'Contains',
                    'HasProperty']


class BratDocument(object):
    def __init__(self, ann_path, txt_path, doc_id, mission, reviewer=''):
        self.ann_path = ann_path
        self.txt_path = txt_path
        self.doc_id = doc_id
        self.mission = mission
        self.reviewer = reviewer
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

            brat_ann = BratAnnotation(ann_line)
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

        return file_content[0]


class BratAnnotation:
    def __init__(self, brat_line):
        record = self.parse_brat_line(brat_line)
        self.ann_id = record['ann_id']
        self.type = record['type']
        self.label = record['label']
        self.start = record['start']
        self.end = record['end']
        self.name = record['name']

    @staticmethod
    def parse_brat_line(brat_line):
        line_tokens = brat_line.strip().split('\t')
        middle_tokens = line_tokens[1].split()

        if line_tokens[0][0] == 'T':
            ann_type = TYPE_ENTITY
        elif line_tokens[0][0] == 'R':
            ann_type = TYPE_RELATION
        else:
            raise RuntimeError('Unrecognized brat ann type: %s' %
                               line_tokens[0][0])

        record = {
            'ann_id': line_tokens[0],
            'type': ann_type,
            'label': middle_tokens[0],
            'start': int(middle_tokens[1]),
            'end': int(middle_tokens[2]),
            'name': canonical_name(line_tokens[2].decode('utf-8'))
        }

        return record
