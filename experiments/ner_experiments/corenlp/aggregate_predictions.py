# python3 

import argparse, sys, os, json, io, pickle
from os.path import join, dirname, abspath, exists
curpath = dirname(abspath(__file__))
parentpath = dirname(curpath)
sys.path.append(parentpath)

from my_name_utils import canonical_elemin_name, canonical_target_name
from extraction_utils import extract_system_entities

from instance import Span_Instance

def get_prediction_docs(prediction_file, tracking_file):
    # first make a list of doc dict 
    docs = {} # keys: docid -> list of sentences -> list of tokens in a sentence 

    prediction_lines = [ line.strip() for line in open(prediction_file,"r").readlines() if line.strip() != ""]
    tracking_lines = [ line.strip() for line in open(tracking_file, "r").readlines() if line.strip() != ""]

    for i, (prediction, track) in enumerate(zip(prediction_lines, tracking_lines)):
        sys.stdout.write(f"\rreading line {i}")
        sys.stdout.flush()
        word, gold_ner_label, ner_label = prediction.split('\t')
        venue, year, docname, sentid, doc_start_char, doc_end_char = track.split("\t")
        docid = (venue, year, docname)
        sentid = int(sentid)
        doc_start_char = int(doc_start_char)
        doc_end_char = int(doc_end_char)

        if docid not in docs:
            docs[docid] = {"sentences": []}
        if sentid >= len(docs[docid]['sentences']):
            assert sentid == len(docs[docid]['sentences']) # make sure sentid is the next sentence
            docs[docid]['sentences'].append({"tokens": [], 'index':sentid})
        tok = {
            'word': word,
            'characterOffsetBegin': doc_start_char,
            'characterOffsetEnd': doc_end_char,
            'ner': ner_label
        }

        docs[docid]['sentences'][sentid]['tokens'].append(tok)
    return docs

def get_entity_from_prediction(prediction_file, tracking_file):

    docs = get_prediction_docs(prediction_file, tracking_file)
    entities = [] 
    for (venue, year, docname), doc in docs.items():
        temp_entities = extract_system_entities(doc = doc)
        for e in temp_entities:
            if e['label'] not in ['Target', 'Element', 'Mineral']:
                continue
            entities.append(Span_Instance(venue, year, docname, e['doc_start_char'], e['doc_end_char'], e['text'], e['label']))
    return entities



if __name__ == "__main__":
    prediction_file = 'saved_models/test.predicted'
    tracking_file = 'data/test.tsv.track'


    entities = get_entity_from_prediction(prediction_file, tracking_file)

    print(f"\nCollected {len(entities)} entities")

    print("Saving to saved_models/test.predicted.entities")
    with open('saved_models/test.predicted.entities', 'wb') as f:
        pickle.dump(entities, f)
