#!/usr/bin/env python
# sqlite.py
# Mars Target Encyclopedia
# Classes and functions to provide access to the MTE database
# (With thanks to Gary Doran for his COSMIC_CTX example)
#
# Kiri Wagstaff
# August 29, 2020
#
# Modification history:
# Steven Lu, 11/05/2020, Add utility functions to ingest brat annotations

import os
import sqlite3
from brat_annotation_sqlite import BratDocument
from brat_annotation_sqlite import TYPE_ENTITY, TYPE_RELATION


class MteDb():

    def __init__(self, dbfile):
        self.dbfile = dbfile
        self.connection = self._connect()

    def _connect(self):
        # If the database file doesn't exist, create and initialize the tables
        needs_init = (not os.path.exists(self.dbfile))
        connection = sqlite3.connect(self.dbfile)
        if needs_init: self._init_db(connection)
        return connection

    def _init_db(self, connection):
        with connection:
            cur = connection.cursor()

            # -------- targets -----------
            cur.execute(
                'CREATE TABLE targets ('
                ' target_id       VARCHAR(90) PRIMARY KEY,' # target_name-mission
                ' target_name     VARCHAR(80),'  # canonical name
                ' mission         VARCHAR(10)'
                ')'
            )

            # -------- components: elements or minerals -----------
            cur.execute(
                'CREATE TABLE components ('
                ' component_name  VARCHAR(80) PRIMARY KEY,'
                ' component_label VARCHAR(80)'
                ')'
            )

            # -------- documents: each document in the collection -----------
            cur.execute(
                'CREATE TABLE documents ('
                ' doc_id          VARCHAR(100) PRIMARY KEY,'  # year_abstractnumber
                ' abstract        INTEGER,'
                ' title           VARCHAR(1024),'
                ' authors         VARCHAR(4096),'
                ' primary_author  VARCHAR(1024),'
                ' affiliations    TEXT,'
                ' venue           TEXT,'
                ' year            INTEGER,'
                ' doc_url         VARCHAR(1024),'
                ' content         TEXT,'
                ' reviewer        VARCHAR(100)'
                ')'
            )

            # -------- contains: link targets to components -----------
            cur.execute(
                'CREATE TABLE contains ('
                ' target_id       VARCHAR(90) REFERENCES targets,'
                ' component_name  VARCHAR(80) REFERENCES components,'
                ' sentence_id     VARCHAR(80) REFERENCES sentences,'
                ' PRIMARY KEY(target_id,component_name,sentence_id)'
                ')'
            )

            # -------- mentions: link targets to sentences in which they appear -----------
            cur.execute(
                'CREATE TABLE mentions ('
                ' target_id       VARCHAR(90) REFERENCES targets,'
                ' sentence_id     VARCHAR(80) REFERENCES sentences,'
                ' PRIMARY KEY(target_id,sentence_id)'
                ')'
            )

            # -------- sentences: sentences used by contains/mentions -----------
            cur.execute(
                'CREATE TABLE sentences ('
                ' doc_id          VARCHAR(100) REFERENCES documents,' # year_abstractnumber
                ' sentence_id     VARCHAR(80) PRIMARY KEY,' # doc_id + sentence_number
                ' sentence        TEXT'
                ')'
            )

    def add_records(self, recs):
        with self.connection:
            cur = self.connection.cursor()
            for rec in recs:
                print('inserting %s' % rec['doc_id'])
                cur.execute(
                    'INSERT OR REPLACE INTO documents ('
                    ' doc_id, abstract, title, authors, primary_author, affiliations,'
                    ' venue, year, doc_url, content'
                    ') VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', 
                    (rec['doc_id'], rec['abstract'], rec['title'], rec['authors'], 
                     rec['primary_author'], rec['affiliations'],
                     rec['venue'], rec['year'], rec['doc_url'],
                     rec['content'])
                )
                cur.executemany(
                    'INSERT OR REPLACE INTO targets ('
                    ' target_id, target_name, mission'
                    ') VALUES (?, ?, ?)',
                    [('%s-%s' % (r[0], r[1]), r[0], r[1]) for r in rec['targets']]
                )
                cur.executemany(
                    'INSERT OR REPLACE INTO components ('
                    ' component_name, component_label'
                    ') VALUES (?, ?)',
                    rec['components']
                )
                # Generate a unique sentence id for each one: doc_id-sentence_index
                sentences = list(set([r[3].strip() for r in rec['contains']]))
                # Add sentences that have mentions of targets, even if no relation is present
                # Assume sentences are bracketed by periods.
                targ_sentences = [rec['content'][max(0, rec['content'].rfind('.', 0, t[2])+1):
                                                 max(t[3]+1, rec['content'].find('.', t[3])+1)].strip()
                                  for t in rec['targets']]
                sentences = list(set(sentences + targ_sentences)) # unique only
                sent_ids = dict(zip(sentences, ['%s-%d' % (rec['doc_id'], n) for n in range(len(sentences))]))
                mentions = zip(['%s-%s' % (t[0], t[1]) for t in rec['targets']], 
                               [sent_ids[s] for s in targ_sentences])
                # Expand each many-to-many contains relation
                # into pairwise relations for storage
                rel_pairs = []
                for r in rec['contains']:
                    for t in r[0]:
                        for c in r[2]:
                            rel_pairs.append(('%s-%s' % (t, r[4]), c, sent_ids[r[3]]))
                cur.executemany(
                    'INSERT OR REPLACE INTO contains ('
                    ' target_id, component_name, sentence_id'
                    ') VALUES (?, ?, ?)',
                    rel_pairs
                )
                cur.executemany(
                    'INSERT OR REPLACE INTO mentions ('
                    ' target_id, sentence_id'
                    ') VALUES (?, ?)',
                    mentions
                )
                cur.executemany(
                    'INSERT OR REPLACE INTO sentences ('
                    ' doc_id, sentence_id, sentence'
                    ') VALUES (?, ?, ?)',
                    [(rec['doc_id'], sent_ids[s], s) for s in sentences]
                )

    @staticmethod
    def targets_insertion(cursor, target_name, mission):
        target_id = '%s-%s' % (target_name, mission)

        sql = """
            INSERT OR REPLACE INTO targets (target_id, target_name, mission) 
            VALUES (?, ?, ?)
        """
        cursor.execute(sql, (target_id, target_name, mission))

        return target_id

    @staticmethod
    def sentences_insertion(cursor, doc_id, sentence):
        # Check if sentence is already in the DB. If so, return its
        # corresponding sentence_id.
        sentence = sentence.decode('utf-8')
        sentence_query = """
            SELECT sentence_id FROM sentences WHERE sentence=?
        """
        cursor.execute(sentence_query, (sentence,))
        sentence_id = cursor.fetchall()
        if len(sentence_id) == 1:
            sentence_id = sentence_id[0][0]
        elif len(sentence_id) > 1:
            raise RuntimeError('There are duplicated sentences in the '
                               'sentences table: %s' % sentence)
        else:
            # sentence_id is created by using doc_id + sentence_index.
            query_sql = """
                SELECT * FROM sentences where doc_id=?
            """
            cursor.execute(query_sql, (doc_id,))
            n_records = len(cursor.fetchall())
            sentence_id = '%s-%d' % (doc_id, n_records)

            insert_sql = """
                INSERT INTO sentences (doc_id, sentence_id, sentence) 
                VALUES (?, ?, ?)
            """
            cursor.execute(insert_sql, (doc_id, sentence_id, sentence))

        return sentence_id

    @staticmethod
    def mentions_insertion(cursor, target_id, sentence_id):
        sql = """
            INSERT OR REPLACE INTO mentions (target_id, sentence_id) 
            VALUES (?, ?)
        """
        cursor.execute(sql, (target_id, sentence_id))

    @staticmethod
    def component_insertion(cursor, component_name, component_label):
        sql = """
            INSERT OR REPLACE INTO components (component_name, component_label) 
            VALUES (?, ?)
        """
        cursor.execute(sql, (component_name, component_label))

    @staticmethod
    def update_reviewer(cursor, doc_id, reviewer):
        sql = """
            UPDATE documents SET reviewer=? WHERE doc_id=?
        """
        cursor.execute(sql, (reviewer, doc_id))

    def insert_brat_doc(self, brat_doc):
        if not isinstance(brat_doc, BratDocument):
            raise TypeError('Cannot insert annotation. The supplied brat_doc '
                            'must be an object of BratDocument')

        cursor = self.connection.cursor()

        # Update the reviewer field in the documents table
        self.update_reviewer(cursor, brat_doc.doc_id, brat_doc.reviewer)

        for brat_ann in brat_doc.ann_content:
            if brat_ann.type == TYPE_ENTITY:
                if brat_ann.label == 'Target':
                    # Extract the sentence in which the target is mentioned.
                    sentence_start_index = max(
                        0,
                        brat_doc.txt_content.rfind('.', 0, brat_ann.start) + 1
                    )
                    sentence_end_index = max(
                        brat_ann.end + 1,
                        brat_doc.txt_content.find('.', brat_ann.end) + 1
                    )
                    sentence = brat_doc.txt_content[sentence_start_index:
                                                    sentence_end_index]

                    try:
                        target_id = self.targets_insertion(
                            cursor, brat_ann.name, brat_doc.mission
                        )

                        sentence_id = self.sentences_insertion(
                            # Remove leading/trailing spaces from sentences
                            cursor, brat_doc.doc_id, sentence.strip()
                        )

                        self.mentions_insertion(cursor, target_id, sentence_id)

                        # Commit all changes to the DB
                        self.connection.commit()
                    except Exception:
                        self.connection.rollback()
                        raise RuntimeError(
                            'Insertion error for target %s in doc %s. ' %
                            (brat_ann.ann_id, brat_doc.doc_id)
                        )
                elif brat_ann.label == 'Element' or brat_ann.label == 'Mineral':
                    try:
                        self.component_insertion(
                            cursor, brat_ann.name, brat_ann.label
                        )
                        self.connection.commit()
                    except Exception:
                        self.connection.rollback()
                        raise RuntimeError(
                            'Insertion error for component %s in doc %s' %
                            (brat_ann.ann_id, brat_doc.doc_id)
                        )
                elif brat_ann.label == 'Property':
                    raise RuntimeError('Not implemented for property label.')
                else:
                    raise RuntimeError('Brat annotation label not recognized: '
                                       '%s' % brat_ann.label)

            elif brat_ann.type == TYPE_RELATION:
                raise RuntimeError('Not implemented for relations.')
            else:
                raise RuntimeError('Brat annotation type not recognized: %s' %
                                   brat_ann.type)

    # Remove existing records related to this brat_doc from `contains`,
    # `mentions`, and `sentences` tables. Records related to the `components`,
    # `targets`, and `documents` tables will not be deleted.
    def partial_delete_brat_doc(self, brat_doc):
        if not isinstance(brat_doc, BratDocument):
            raise TypeError('Cannot update annotation. The supplied brat_doc '
                            'must be an object of BratDocument')

        cursor = self.connection.cursor()

        try:
            contains_delete_sql = """
                DELETE FROM contains 
                WHERE sentence_id IN (
                  SELECT c.sentence_id FROM contains AS c 
                  INNER JOIN sentences AS s ON c.sentence_id=s.sentence_id 
                  INNER JOIN documents AS d ON s.doc_id=d.doc_id 
                  WHERE d.doc_id=?
                );
            """
            cursor.execute(contains_delete_sql, (brat_doc.doc_id,))

            mentions_delete_sql = """
                DELETE FROM mentions 
                WHERE sentence_id IN (
                  SELECT m.sentence_id FROM mentions AS m 
                  INNER JOIN sentences AS s ON m.sentence_id=s.sentence_id 
                  INNER JOIN documents AS d ON s.doc_id=d.doc_id 
                  WHERE d.doc_id=?
                );
            """
            cursor.execute(mentions_delete_sql, (brat_doc.doc_id,))

            sentences_delete_sql = """
                DELETE FROM sentences WHERE doc_id=?
            """
            cursor.execute(sentences_delete_sql, (brat_doc.doc_id,))

            # Commit the changes when all deletions were successful.
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise RuntimeError(
                'Encountered problems to delete records related to doc_id %s '
                'from `contains`, `mentions`, or `sentences` table. Rolling '
                'back any changes made to the database.' % brat_doc.doc_id
            )

    def update_brat_doc(self, brat_doc):
        if not isinstance(brat_doc, BratDocument):
            raise TypeError('Cannot update annotation. The supplied brat_doc '
                            'must be an object of BratDocument')
        # Partially delete the brat_doc from the MTE DB
        self.partial_delete_brat_doc(brat_doc)

        # Insert the brat_doc into MTE DB
        self.insert_brat_doc(brat_doc)

    def get_document_by_doc_id(self, doc_id):
        with self.connection:
            cursor = self.connection.cursor()
            query_sql = """
                SELECT * FROM documents WHERE doc_id=?
            """
            cursor.execute(query_sql, (doc_id,))
            doc = cursor.fetchall()

        return doc

    def remove_orphaned_targets(self):
        cursor = self.connection.cursor()

        target_removal_sql = """
            DELETE FROM targets WHERE target_id NOT IN 
            (SELECT target_id FROM mentions)
        """

        cursor.execute(target_removal_sql)
        self.connection.commit()

        return cursor.rowcount

    def remove_orphaned_components(self):
        cursor = self.connection.cursor()

        components_removal_sql = """
            DELETE FROM components WHERE component_name NOT IN 
            (SELECT component_name FROM contains)
        """

        cursor.execute(components_removal_sql)
        self.connection.commit()

        return cursor.rowcount

    def remove_orphaned_documents(self):
        cursor = self.connection.cursor()

        documents_removal_sql = """
            DELETE FROM documents WHERE doc_id NOT IN 
            (SELECT doc_id FROM sentences)
        """

        cursor.execute(documents_removal_sql)
        self.connection.commit()

        return cursor.rowcount

    def close(self):
        self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
