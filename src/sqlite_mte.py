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
                ' target_name     VARCHAR(80),'  # verbatim
                ' mission         VARCHAR(10)'
                ')'
            )

            # -------- aliases -----------
            cur.execute(
                'CREATE TABLE aliases ('
                ' target_name     VARCHAR(80) PRIMARY KEY,'  # verbatim
                ' canonical_name  VARCHAR(80)'
                ')'
            )

            # -------- components: elements or minerals -----------
            cur.execute(
                'CREATE TABLE components ('
                ' component_name  VARCHAR(80) PRIMARY KEY,'
                ' component_label VARCHAR(80)'
                ')'
            )

            # -------- properties -----------
            cur.execute(
                'CREATE TABLE properties ('
                ' property_name  VARCHAR(80) PRIMARY KEY'
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
                ' target_sentence_id     VARCHAR(80) REFERENCES sentences,'
                ' component_sentence_id  VARCHAR(80) REFERENCES sentences,'
                ' PRIMARY KEY(target_id,component_name,target_sentence_id,component_sentence_id)'
                ')'
            )

            # -------- has_property: link targets to properties -----------
            cur.execute(
                'CREATE TABLE has_property ('
                ' target_id        VARCHAR(90) REFERENCES targets,'
                ' property_name    VARCHAR(80) REFERENCES properties,'
                ' target_sentence_id    VARCHAR(80) REFERENCES sentences,'
                ' property_sentence_id  VARCHAR(80) REFERENCES sentences,'
                ' PRIMARY KEY(target_id,property_name,target_sentence_id,property_sentence_id)'
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
                    [(u'%s-%s' % (r[0], r[1]), r[0], r[1]) for r in rec['targets']]
                )
                cur.executemany(
                    'INSERT OR REPLACE INTO components ('
                    ' component_name, component_label'
                    ') VALUES (?, ?)',
                    rec['components']
                )
                # Here's where we would insert properties, 
                # but the NER model (in .json file) won't have any.

                # Generate a unique id for each sentence: doc_id-sentence_index
                sentences = list(set([r[3].strip() for r in rec['contains']]))
                # Add sentences that have mentions of targets, 
                # even if no relation is present
                # Assume sentences are bracketed by periods.
                targ_sentences = [rec['content'][max(0, rec['content'].rfind('.', 0, t[2])+1):
                                                 max(t[3]+1, rec['content'].find('.', t[3])+1)].strip()
                                  for t in rec['targets']]
                sentences = list(set(sentences + targ_sentences)) # unique only
                sent_ids = dict(zip(sentences, 
                                    ['%s-%d' % (rec['doc_id'], n) 
                                     for n in range(len(sentences))]))
                mentions = zip(['%s-%s' % (t[0], t[1]) 
                                for t in rec['targets']], 
                               [sent_ids[s] for s in targ_sentences])

                # Expand each many-to-many contains relation
                # into pairwise relations for storage
                rel_pairs = []
                for r in rec['contains']:
                    for t in r[0]:
                        for c in r[2]:
                            # These auto-generated contains relations
                            # are constrained to be within-sentence, so
                            # target_sentence_id = component_sentence_id
                            rel_pairs.append(('%s-%s' % (t, r[4]), c,
                                              sent_ids[r[3]], sent_ids[r[3]]))
                cur.executemany(
                    'INSERT OR REPLACE INTO contains ('
                    ' target_id, component_name,'
                    ' target_sentence_id, component_sentence_id'
                    ') VALUES (?, ?, ?, ?)',
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
    def alias_insertion(cursor, verbatim_target, canonical_target):
        sql = """
            INSERT OR REPLACE INTO aliases (target_name, canonical_name) 
            VALUES (?, ?)
        """

        cursor.execute(sql, (verbatim_target, canonical_target))

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
        sentence_query = """
            SELECT sentence_id FROM sentences WHERE sentence=? AND doc_id=?
        """
        cursor.execute(sentence_query, (sentence, doc_id))
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

    # Add a relation, assuming the argument is a name (not id)
    @staticmethod
    def relation_insertion(cursor, table_name, target_id, arg_name,
                           target_sentence_id, arg_sentence_id):
        sql = """
            INSERT OR REPLACE INTO %s (target_id, %s, target_sentence_id, %s)
            VALUES (?, ?, ?, ?)
        """
        if table_name == 'contains':
            arg_column = 'component_name'
            arg_id_column = 'component_sentence_id'
        elif table_name == 'has_property':
            arg_column = 'property_name'
            arg_id_column = 'property_sentence_id'
        else:
            raise RuntimeError('Unknown table name %s' % table_name)
        cursor.execute(sql % (table_name, arg_column, arg_id_column), 
                       (target_id, arg_name,
                        target_sentence_id, arg_sentence_id))

    @staticmethod
    def component_insertion(cursor, component_name, component_label):
        sql = """
            INSERT OR REPLACE INTO components (component_name, component_label) 
            VALUES (?, ?)
        """
        cursor.execute(sql, (component_name, component_label))

    @staticmethod
    def property_insertion(cursor, property_name):
        sql = """
            INSERT OR REPLACE INTO properties (property_name) 
            VALUES (?)
        """
        cursor.execute(sql, (property_name,))

    @staticmethod
    def get_sentence(brat_doc, brat_ann):
        # Search backward for a period followed by a space
        # or a capital letter or double quotes
        prev_period = brat_doc.txt_content.rfind('.', 0, brat_ann.start)
        while (prev_period > 0 and
               brat_doc.txt_content[prev_period + 1] != ' ' and
               # Allow period + capital letter starting next sentence
               not brat_doc.txt_content[prev_period + 1].isupper() and
                # Allow period + "
               brat_doc.txt_content[prev_period + 1] != '"'):
            prev_period = brat_doc.txt_content.rfind('.', 0, prev_period - 1)
        # If last sentence ended in period + " then skip the " too
        if brat_doc.txt_content[prev_period + 1] == '"':
            prev_period += 1
            
        sentence_start_index = max(0, prev_period + 1)

        # Search forward for a period followed by a space, double quote,
        # or capital letter
        next_period = brat_doc.txt_content.find('.', brat_ann.end)
        while (brat_doc.txt_content[next_period + 1] != ' ' and
               not brat_doc.txt_content[next_period + 1].isupper() and
               brat_doc.txt_content[next_period + 1] != '"'):
            next_period = brat_doc.txt_content.find('.', next_period + 1)
        # If this sentence ends in period + " then include the " too
        if brat_doc.txt_content[next_period + 1] == '"':
            next_period += 1
        
        sentence_end_index = max(brat_ann.end + 1,
                                 next_period + 1)

        sentence = brat_doc.txt_content[sentence_start_index:
                                        sentence_end_index]
        return sentence

    
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
                    sentence = self.get_sentence(brat_doc, brat_ann)

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
                    except Exception as e:
                        self.connection.rollback()
                        raise RuntimeError(
                            'Insertion error for target %s in doc %s: %s' %
                            (brat_ann.ann_id, brat_doc.doc_id, e)
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
                    try:
                        self.property_insertion(
                            cursor, brat_ann.name
                        )
                        self.connection.commit()
                    except Exception as e:
                        self.connection.rollback()
                        raise RuntimeError(
                            'Insertion error for property %s (%s) in doc %s, %s' %
                            (brat_ann.ann_id, brat_ann.name, brat_doc.doc_id, e)
                        )
                else:
                    raise RuntimeError('Brat annotation label not recognized: '
                                       '%s' % brat_ann.label)

            elif brat_ann.type == TYPE_RELATION:

                # Look up arg1 (Target)
                target_ann = [ba for ba in brat_doc.ann_content
                              if ba.ann_id == brat_ann.arg1]
                if len(target_ann) == 0:
                    print('Warning: %s: No annotation found for %s;'
                          ' skipping this relation' %
                          (brat_doc.doc_id, brat_ann.arg1))
                    continue
                    #raise RuntimeError('%s: No annotation found for %s' %
                    #                   (brat_doc.doc_id, brat_ann.arg1))
                target_ann = target_ann[0]
                target_id = target_ann.name + '-' + brat_doc.mission

                # Look up arg2 (e.g., Component or Property)
                arg2_ann = [ba for ba in brat_doc.ann_content
                            if ba.ann_id == brat_ann.arg2]
                if len(arg2_ann) == 0:
                    raise RuntimeError('%s: No annotation found for %s' %
                                       (brat_doc.doc_id, brat_ann.arg2))
                arg2_ann = arg2_ann[0]

                # Look up the sentence for the Target and Component/Property
                target_sentence = self.get_sentence(brat_doc, target_ann)
                target_sentence_id = self.sentences_insertion(
                    cursor, brat_doc.doc_id, target_sentence.strip())
                arg2_sentence = self.get_sentence(brat_doc, arg2_ann)
                arg2_sentence_id = self.sentences_insertion(
                    cursor, brat_doc.doc_id, arg2_sentence.strip())

                # Add to the appropriate table
                if brat_ann.label == 'Contains':
                    relation = 'contains'
                elif brat_ann.label == 'HasProperty':
                    relation = 'has_property'
                else:
                    raise RuntimeError('%s: Relation %s not yet supported' % 
                                       (brat_doc.doc_id, brat_ann.label))
                self.relation_insertion(cursor, relation,
                                        target_id, arg2_ann.name,
                                        target_sentence_id, arg2_sentence_id)

            else:
                raise RuntimeError('%s: Brat annotation type not recognized: %s' %
                                   (brat_doc.doc_id, brat_ann.type))

    # Remove existing records related to this brat_doc from `contains`,
    # `mentions`, and `sentences` tables. Records related to the `components`,
    # `targets`, and `documents` tables will not be deleted.
    def partial_delete_brat_doc(self, brat_doc):
        if not isinstance(brat_doc, BratDocument):
            raise TypeError('Cannot update annotation. The supplied brat_doc '
                            'must be an object of BratDocument')

        cursor = self.connection.cursor()

        try:
            # Delete all contains relations with target sentences
            # in this document
            contains_delete_sql = """
                DELETE FROM contains 
                WHERE target_sentence_id IN (
                  SELECT c.target_sentence_id FROM contains AS c 
                  INNER JOIN sentences AS s ON c.target_sentence_id=s.sentence_id 
                  INNER JOIN documents AS d ON s.doc_id=d.doc_id 
                  WHERE d.doc_id=?
                );
            """
            cursor.execute(contains_delete_sql, (brat_doc.doc_id,))

            # Delete all has_property relations with target sentences
            # in this document
            has_property_delete_sql = """
                DELETE FROM has_property 
                WHERE target_sentence_id IN (
                  SELECT c.target_sentence_id FROM has_property AS c 
                  INNER JOIN sentences AS s ON c.target_sentence_id=s.sentence_id 
                  INNER JOIN documents AS d ON s.doc_id=d.doc_id 
                  WHERE d.doc_id=?
                );
            """
            cursor.execute(has_property_delete_sql, (brat_doc.doc_id,))

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
        except Exception as e:
            self.connection.rollback()
            raise RuntimeError(
                'Encountered problems to delete records related to doc_id %s '
                'from `contains`, `mentions`, or `sentences` table. Rolling '
                'back any changes made to the database.' % brat_doc.doc_id, e
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

    def remove_orphaned_properties(self):
        cursor = self.connection.cursor()

        properties_removal_sql = """
            DELETE FROM properties WHERE property_name NOT IN 
            (SELECT property_name FROM has_property)
        """

        cursor.execute(properties_removal_sql)
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

    def add_known_target(self, target_name, mission):
        cursor = self.connection.cursor()
        target_id = self.targets_insertion(cursor, target_name, mission)
        self.connection.commit()

        return target_id

    def add_alias(self, verbatim_target, canonical_target):
        cursor = self.connection.cursor()
        self.alias_insertion(cursor, verbatim_target, canonical_target)
        self.connection.commit()

    def close(self):
        self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
