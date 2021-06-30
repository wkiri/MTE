# This function makes within sentence instances and removes duplicates based on texts
import re, pickle, sys, argparse, random, json, os
from sys import stdout
from copy import deepcopy 
from os.path import abspath, dirname, join, exists
from os import makedirs, listdir

curpath = dirname(abspath(__file__))
upperpath = dirname(curpath)
sys.path.append(upperpath)

from instance import Span_Instance

from config import label2ind, ind2label,  tokenizer_type

parentpath = dirname(upperpath)
sys.path.insert(0, parentpath)
from extraction_utils import get_docid, extract_gold_entities_from_ann,extract_intrasent_entitypairs_from_text_file, extract_intrasent_goldrelations_from_ann, extract_entities_from_text, get_offset2sentid, get_sentid_from_offset


from transformers import *


def add_marker_tokens(tokenizer, ner_labels):
    new_tokens = []
    for label in ner_labels:
        new_tokens.append('<ner_start=%s>'%label.lower())
        new_tokens.append('<ner_end=%s>'%label.lower())
    tokenizer.add_tokens(new_tokens)


def make_instances( tokenizer, ann_files, text_files, corenlp_files, outdir, max_len = 512, extra_num = 0, is_training = False, use_sys_ners = False):

    # first collect all valid entity for predictions. this is instance-based, which only relies on character offset. And it only extracts spans that cooccur with target in a sentence
    gold_spanins = [] # stores entities that are in a gold relation in annotation. used for evaluation 

    seen_goldids = set()
    for text_file, ann_file, corenlp_file in zip(text_files, ann_files, corenlp_files):

        intrasent_gold_relations = [(e1, e2, relation) for e1, e2, relation in extract_intrasent_goldrelations_from_ann(ann_file, corenlp_file = corenlp_file) if relation == 'Contains' and e1['label'] == 'Target' and e2['label'] in ['Element', 'Mineral']]

        for e1, e2, relation in intrasent_gold_relations:

            span2 = Span_Instance(e2['venue'], e2['year'], e2['docname'], e2['doc_start_char'], e2['doc_end_char'], e2['text'], 'Component') # specifically assign component 
            span2.relation_label = 'Contains'
            
            if e2['label'] in ['Element', 'Mineral', 'Component'] and span2.span_id not in seen_goldids:
                seen_goldids.add(span2.span_id)
                gold_spanins.append(span2)


    spanins = []
    seen_spanids = set()
    exceed_len_cases = 0 
    added_extra = 0 
    total_added_extra = extra_num * len(seen_goldids)
    pseudo_positive_training = []
    for text_file, ann_file, corenlp_file in zip(text_files, ann_files, corenlp_files):

        doc = json.load(open(corenlp_file))

        for e1, e2 in extract_intrasent_entitypairs_from_text_file(text_file, ann_file, doc = doc, use_sys_ners = use_sys_ners, use_component = True):

            sentid = e1['sentid']
            if e1['label'] != 'Target' or e2['label'] not in ['Element', 'Mineral', 'Component']:
                continue

            sent_toks = [token['word'] for token in doc['sentences'][sentid]['tokens']]
    

            span2 = Span_Instance(e2['venue'], e2['year'], e2['docname'], e2['doc_start_char'], e2['doc_end_char'], e2['text'], 'Component', sent_toks = deepcopy(sent_toks), sentid = sentid, sent_start_idx = e2['sent_start_idx'], sent_end_idx = e2['sent_end_idx'])

            
            if e2['label'] in ['Element', 'Mineral', 'Component']  and span2.span_id not in seen_spanids :
                exceed = span2.insert_type_markers(tokenizer, max_len = max_len)
                span2.relation_label = 'Contains' if span2.span_id in seen_goldids else 'O'
                spanins.append(span2)
                seen_spanids.add(span2.span_id)
                exceed_len_cases += exceed


       
        if is_training:
            posins_ids = set([(s.venue, s.year, s.docname, s.sentid, s.std_text) for s in spanins if s.relation_label != 'O'])
            
            for s in spanins:
                if (s.venue, s.year, s.docname, s.sentid, s.std_text) in posins_ids:

                    if s.relation_label == 'O':
                        pseudo_positive_training.append(s)
                    s.relation_label = 'Contains'
    if is_training:
        with open("pseudo_positive_training.txt", "w") as f:
            f.write("\n\n".join([f"{i}. {s}" for i, s in enumerate( pseudo_positive_training)]))

    print(f"generated {len(spanins)} extracted instances with {len([s for s in spanins if s.relation_label != 'O'])} positive, and {exceed_len_cases} of these exceed max_len")
    print(f"generated {len(gold_spanins)} gold instances")

    intersection = len(set([s.span_id for s in spanins]).intersection(seen_goldids))/len(seen_goldids)
    print(f"{intersection*100:.2f}% gold spans are matched ")

    print("possible ner labels: ", set([s.ner_label for s in spanins]), set(s.ner_label for s in gold_spanins))
            



    if not exists(outdir):
        os.makedirs(outdir)

    outfile = join(outdir, f"spanins.pkl")
    print(f"Saving to {outfile}")
    with open(outfile, "wb") as f:
        pickle.dump(spanins, f)

    outfile = join(outdir, f"gold_spanins.pkl")
    print(f"Saving the evaluation set to {outfile}")
    with open(outfile, "wb") as f:
        pickle.dump(gold_spanins, f)

    print()

def main(args):

    tokenizer = BertTokenizerFast.from_pretrained(tokenizer_type)

    ners = ['Component']

    add_marker_tokens(tokenizer, ners)

    proj_path = dirname(dirname(dirname(dirname(curpath))))
    datadir_prefix = join(proj_path, "corpus-LPSC")
    corenlpdir_prefix = join(proj_path, 'parse')
    corenlpdir_sysner_prefix = join(proj_path, 'parse-with-sysners')


    # ---- make training samples ----


    ann15_indir = join(datadir_prefix, "lpsc15-C-raymond-sol1159-v3-utf8")
    corenlp15_indir = join(corenlpdir_prefix, "lpsc15-C-raymond-sol1159-v3-utf8")
    corenlp15_sysner_indir = join(corenlpdir_sysner_prefix, "lpsc15-C-raymond-sol1159-v3-utf8")

    train_annfiles = [join(ann15_indir, file) for file in listdir(ann15_indir) if file.endswith(".ann")][:42]
    train_textfiles = [join(ann15_indir, file.split(".ann")[0] + ".txt") for file in train_annfiles]
    train_corenlpfiles = [join(corenlp15_indir, file.split("/")[-1].split(".ann")[0] + ".txt.json") for file in train_annfiles]

    assert all([exists(k) for k in train_annfiles + train_textfiles + train_corenlpfiles])
    
    print("> Making TRAIN data using gold NER")
    outdir = "ins/train"
    make_instances(tokenizer, train_annfiles, train_textfiles, train_corenlpfiles, outdir, max_len = 512, is_training = True, use_sys_ners = False)
    # ---- make val samples ----
  
    dev_annfiles = [join(ann15_indir, file) for file in listdir(ann15_indir) if file.endswith(".ann")][42:]
    dev_textfiles = [join(ann15_indir, file.split(".ann")[0] + ".txt") for file in dev_annfiles]
    dev_corenlpfiles = [join(corenlp15_indir, file.split("/")[-1].split(".ann")[0] + ".txt.json") for file in dev_annfiles]

    dev_corenlp_sysner_files = [join(corenlp15_sysner_indir, file.split("/")[-1].split(".ann")[0] + ".txt.json") for file in dev_annfiles]
    assert all([exists(k) for k in dev_annfiles + dev_textfiles + dev_corenlpfiles])

    print("> Making DEV data using gold NER")
    outdir = "ins/dev/gold_ner"
    make_instances( tokenizer, dev_annfiles, dev_textfiles, dev_corenlpfiles, outdir, max_len = 512, use_sys_ners = False)
    print("> Making DEV data using system NER")
    outdir = "ins/dev/sys_ner"
    make_instances( tokenizer, dev_annfiles, dev_textfiles, dev_corenlp_sysner_files, outdir, max_len = 512, use_sys_ners = True)

    # -------- make test samples ---------
    print(" ----- making test samples ... ")

    test_venues = args.test_venues
    
    test_annfiles = []
    test_textfiles = []
    test_corenlpfiles = []
    test_corenlp_sysner_files = [] 
    for venue in test_venues:
        ann_files =[join(datadir_prefix, venue, file) for file in listdir(join(datadir_prefix, venue)) if file.endswith(".ann")]

        text_files = [file.split(".ann")[0] + ".txt" for file in ann_files]

        corenlp_files =[join(corenlpdir_prefix, venue, file.split("/")[-1] + ".json") for file in text_files]

        corenlp_sysner_files =[join(corenlpdir_sysner_prefix, venue, file.split("/")[-1] + ".json") for file in text_files]

        test_annfiles.extend(ann_files)
        test_textfiles.extend(text_files)
        test_corenlpfiles.extend(corenlp_files)
        test_corenlp_sysner_files.extend(corenlp_sysner_files)

    assert all([exists(k) for k in test_annfiles + test_textfiles + test_corenlpfiles])

    print("> Making TEST data using gold NER")
    outdir = "ins/test/gold_ner"
    make_instances( tokenizer, test_annfiles, test_textfiles, test_corenlpfiles, outdir, max_len = 512, use_sys_ners = False)

    print("> Making TEST data using system NER")
    outdir = "ins/test/sys_ner"
    make_instances(tokenizer, test_annfiles, test_textfiles, test_corenlp_sysner_files, outdir, max_len = 512, use_sys_ners = True)

    tokenizer.save_vocabulary("ins")

# python make_train_val_test.py > ./stat/train_dev_test.txt
if __name__ == "__main__":
    # make training/val/test instances, and gold spans

    parser = argparse.ArgumentParser()

    parser.add_argument('--test_venues', nargs = "+", required = True)




    args = parser.parse_args()
    main(args)
