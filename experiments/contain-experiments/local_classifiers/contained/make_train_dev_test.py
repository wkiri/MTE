# This function makes within sentence instances and removes duplicates based on texts
import re, pickle, sys, argparse, random, json, os
from sys import stdout
from copy import deepcopy 
from os.path import abspath, dirname, join, exists
from os import makedirs, listdir

# curpath = dirname(abspath(__file__))
curpath = abspath(".")
upperpath = dirname(curpath)
sys.path.append(upperpath)
from instance import Span_Instance


from config import label2ind, ind2label,  tokenizer_type

parentpath = dirname(upperpath)
sys.path.insert(0, parentpath)
from extraction_utils import get_docid, extract_gold_entities_from_ann,extract_intrasent_entitypairs_from_text_file, extract_intrasent_goldrelations_from_ann, extract_entities_from_text, get_offset2sentid, get_sentid_from_offset


from transformers import *
tokenizer = BertTokenizerFast.from_pretrained(tokenizer_type)

def make_instances(mode, ann_files, text_files, corenlp_files, outdir, max_len = 512):

    # first collect all valid entity for predictions. this is instance-based, which only relies on character offset. extract spans that cooccur with target in a sentence
    gold_spanins = []
    seen_goldids = set()
    for text_file, ann_file, corenlp_file in zip(text_files, ann_files, corenlp_files):

        intrasent_gold_relations = [(e1, e2, relation) for e1, e2, relation in extract_intrasent_goldrelations_from_ann(ann_file, corenlp_file = corenlp_file) if relation == 'Contains' and e1['label'] == 'Target' and e2['label'] in ['Element', 'Mineral']]

        for e1, e2, relation in intrasent_gold_relations:
            span1 = Span_Instance(e1['venue'], e1['year'], e1['docname'], e1['doc_start_char'], e1['doc_end_char'], e1['text'], e1['label'])
            span1.relation_label = 'Contains'
            span2 = Span_Instance(e2['venue'], e2['year'], e2['docname'], e2['doc_start_char'], e2['doc_end_char'], e2['text'], e2['label'])
            span2.relation_label = 'Contains'
            if (mode == 'Merged' or mode == 'T') and span1.span_id not in seen_goldids:
                seen_goldids.add(span1.span_id)
                gold_spanins.append(span1)
            if (mode == 'Merged' or e2['label'][0] in mode) and span2.span_id not in seen_goldids:
                seen_goldids.add(span2.span_id)
                gold_spanins.append(span2)


    spanins = []
    seen_spanids = set()
    for text_file, ann_file, corenlp_file in zip(text_files, ann_files, corenlp_files):

        doc = json.load(open(corenlp_file))

        entities = [e for e in extract_entities_from_text(text_file, ann_file, corenlp_file = corenlp_file) if e['label'] in ['Target', 'Element', 'Mineral']]


        sentid2entities = {}
        for e in entities:
            if e['sentid'] not in sentid2entities:
                sentid2entities[e['sentid']] = []
            sentid2entities[e['sentid']].append(deepcopy(e))

        for sentid in sentid2entities:
            ners =  [e['label'] for e in sentid2entities[sentid]]
            if 'Target' not in ners or ('Element' not in ners and 'Mineral' not in ners):
                continue

            sent_toks = [token['word'] for token in doc['sentences'][sentid]['tokens']]
    
            for e in sentid2entities[sentid]:

                span = Span_Instance(e['venue'], e['year'], e['docname'], e['doc_start_char'], e['doc_end_char'], e['text'], e['label'], sent_toks = deepcopy(sent_toks), sentid = sentid, sent_start_idx = e['sent_start_idx'], sent_end_idx = e['sent_end_idx'])



                if span.span_id in seen_goldids:
                    span.relation_label = 'Contains'
                else:
                    span.relation_label = 'O'

                success = span.insert_type_markers(tokenizer, max_len = max_len)

                
                if success and (mode == 'Merged' or e['label'][0] in mode) and span.span_id not in seen_spanids:
                    spanins.append(span)
                    seen_spanids.add(span.span_id)



    if not exists(outdir):
        os.makedirs(outdir)

    outfile = join(outdir, f"{mode}.extracted_gold_spanins.pkl")
    print(f"saving to {outfile}")
    with open(outfile, "wb") as f:
        pickle.dump(spanins, f)

    outfile = join(outdir, f"{mode}.annotated_gold_spanins.pkl")
    print(f"saving the evaluation set to {outfile}")
    with open(outfile, "wb") as f:
        pickle.dump(gold_spanins, f)

    print()

def main(args):
    mode = args.mode

    proj_path = dirname(dirname(dirname(dirname(curpath))))
    datadir_prefix = join(proj_path, "corpus-LPSC")
    corenlpdir_prefix = join(proj_path, 'parse')
    print(corenlpdir_prefix)

    # ---- make training samples ----
    print(" ----- making training samples ... ")

    ann15_indir = join(datadir_prefix, "lpsc15-C-raymond-sol1159-v3-utf8")
    corenlp15_indir = join(corenlpdir_prefix, "lpsc15-C-raymond-sol1159-v3-utf8")

    train_annfiles = [join(ann15_indir, file) for file in listdir(ann15_indir) if file.endswith(".ann")][:42]
    train_textfiles = [join(ann15_indir, file.split(".ann")[0] + ".txt") for file in train_annfiles]
    train_corenlpfiles = [join(corenlp15_indir, file.split("/")[-1].split(".ann")[0] + ".txt.json") for file in train_annfiles]

    assert all([exists(k) for k in train_annfiles + train_textfiles + train_corenlpfiles])
    
    outdir = "ins/train"
    make_instances(mode, train_annfiles, train_textfiles, train_corenlpfiles, outdir, max_len = 512)
    # ---- make val samples ----
    print(" ----- making dev samples ... ")
  
    dev_annfiles = [join(ann15_indir, file) for file in listdir(ann15_indir) if file.endswith(".ann")][42:]
    dev_textfiles = [join(ann15_indir, file.split(".ann")[0] + ".txt") for file in dev_annfiles]
    dev_corenlpfiles = [join(corenlp15_indir, file.split("/")[-1].split(".ann")[0] + ".txt.json") for file in dev_annfiles]
    assert all([exists(k) for k in dev_annfiles + dev_textfiles + dev_corenlpfiles])

    outdir = "ins/dev"
    make_instances(mode, dev_annfiles, dev_textfiles, dev_corenlpfiles, outdir, max_len = 512)

    # -------- make test samples ---------
    print(" ----- making test samples ... ")

    test_venues = args.test_venues
    
    test_annfiles = []
    test_textfiles = []
    test_corenlpfiles = []
    for venue in test_venues:
        ann_files =[join(datadir_prefix, venue, file) for file in listdir(join(datadir_prefix, venue)) if file.endswith(".ann")]

        text_files = [file.split(".ann")[0] + ".txt" for file in ann_files]

        corenlp_files =[join(corenlpdir_prefix, venue, file.split("/")[-1] + ".json") for file in text_files]

        test_annfiles.extend(ann_files)
        test_textfiles.extend(text_files)
        test_corenlpfiles.extend(corenlp_files)

    assert all([exists(k) for k in test_annfiles + test_textfiles + test_corenlpfiles])

    outdir = "ins/test"
    make_instances(mode, test_annfiles, test_textfiles, test_corenlpfiles, outdir, max_len = 512)

# python make_train_val_test.py > ./stat/train_dev_test.txt
if __name__ == "__main__":
    # make training/val/test instances, and gold spans

    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices = ["Merged", "EM", "ET", "MT", "E", "M", "T"], help = "what experiments to run (e.g., elements, minerals, and their merged set)", default = 'EM')

    parser.add_argument('--test_venues', nargs = "+", required = True)

    args = parser.parse_args()
    main(args)
