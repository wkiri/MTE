#!/usr/bin/env python
# update_sqlite.py
# Mars Target Encyclopedia
# Read in human-reviewed brat annotations and update the MTE sqlite database
#
# Steven Lu
# October 22, 2020
# Copyright notice at bottom of file.

import os
import sys
from sqlite_mte import MteDb
from brat_annotation_sqlite import BratDocument
from name_utils import canonical_target_name


def doc_exists(mte_db, doc_id):
    doc = mte_db.get_document_by_doc_id(doc_id)
    if len(doc) == 1:
        return True
    elif len(doc) == 0:
        return False
    else:
        raise RuntimeError('There can be only one document per doc_id')


def main(ann_dir, db_file, mission, reviewer, remove_orphans, target_list):
    if not os.path.exists(ann_dir) or not os.path.isdir(ann_dir):
        print '[ERROR] Annotation directory does not exist: %s' % \
              os.path.abspath(ann_dir)
        sys.exit(1)

    if not os.path.exists(db_file) or not os.path.isfile(db_file):
        print '[ERROR] Database file does not exist: %s' % \
              os.path.abspath(db_file)
        sys.exit(1)

    # Get all the .ann files
    ann_list = [fn for fn in os.listdir(ann_dir) if fn.endswith('.ann')]

    # Create MTE DB
    mte_db = MteDb(db_file)

    print '[INFO] Updating the MTE DB file (%s) with %d reviewed brat ' \
          'annotations in %s directory.' % (os.path.abspath(db_file),
                                            len(ann_list),
                                            os.path.abspath(ann_dir))

    for idx, ann_file in enumerate(ann_list):
        print '[INFO] %d/%d Processing %s' % (idx + 1, len(ann_list), ann_file)

        # Document id is the ann file name without .ann extension
        doc_id = ann_file[:-4]

        # Get ann and txt file paths (assuming the ann and txt files are in the
        # same directory)
        ann_path = os.path.join(ann_dir, ann_file)
        txt_path = os.path.join(ann_dir, '%s.txt' % doc_id)

        # Create BratDocument object - read txt file and parse ann file
        brat_doc = BratDocument(ann_path, txt_path, doc_id, mission, reviewer)

        if doc_exists(mte_db, doc_id):
            mte_db.update_brat_doc(brat_doc)
        else:
            print '[WARNING] Document %s does not exist in the DB. Skip.' % \
                  doc_id

    if remove_orphans:
        print '[INFO] --remove_orphans is enabled. Working on removing orphans.'

        counts = mte_db.remove_orphaned_targets()
        print '[INFO] Orphaned targets removed: %d' % counts

        counts = mte_db.remove_orphaned_components()
        print '[INFO] Orphaned components removed: %d' % counts

        counts = mte_db.remove_orphaned_properties()
        print '[INFO] Orphaned properties removed: %d' % counts

        counts = mte_db.remove_orphaned_documents()
        print '[INFO] Orphaned documents removed: %d' % counts

    if target_list is not None:
        if not os.path.exists(target_list):
            print '[ERROR] Target list not found: %s' % \
                  os.path.abspath(target_list)
            sys.exit(1)

        with open(target_list, 'r') as f:
            known_targets = f.readlines()
            known_targets = [kt.strip() for kt in known_targets]

        for kt in known_targets:
            mte_db.add_known_target(canonical_target_name(kt), mission)

        print '[INFO] Known mission targets from the target list %s have ' \
              'been added to the DB file.' % os.path.abspath(target_list)

    mte_db.close()
    print '[INFO] DONE.'


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Read in human-reviewed brat '
                                                 'annotations and update the '
                                                 'MTE sqlite database')
    parser.add_argument('ann_dir', type=str,
                        help='Path to the directory that contains .ann files')
    parser.add_argument('db_file', type=str,
                        help='Path to the MTE sqlite DB file')
    parser.add_argument('mission', type=str, choices=['mpf', 'phx', 'msl'],
                        help='Mission that the documents belong to.')
    parser.add_argument('-r', '--reviewer', type=str, default='',
                        help='(Optional) The name of the person who reviewed '
                        'the annotations in the ann_dir directory. Default is '
                        'an empty string')
    parser.add_argument('-ro', '--remove_orphans', default=False,
                        action='store_true', help='A flag to remove orphaned '
                        'components, and documents when enabled. The '
                        'default is disabled.')
    parser.add_argument('-tl', '--target_list', type=str,
                        help='(Optional) Path to a known mission target list. '
                             'If the path is provided, the target names in the '
                             'known mission will be added to the DB file.')

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
