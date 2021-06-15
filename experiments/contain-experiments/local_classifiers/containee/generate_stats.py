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
parentpath = dirname(upperpath)
sys.path.insert(0, parentpath)
from extraction_utils import get_docid, extract_gold_entities_from_ann,extract_intrasent_entitypairs_from_text_file, extract_intrasent_goldrelations_from_ann, extract_entities_from_text, get_offset2sentid, get_sentid_from_offset


def percentage_gold_nested_entities(train_annfiles, dev_annfiles, test_annfiles):
    for ann_files, name in zip([train_annfiles, dev_annfiles, test_annfiles], ["TRAIN", 'DEV', 'TEST']):
        overlap_count = 0
        gold_count = 0
        single_count = 0

        for ann_file in ann_files:
            offset2entities = {}

            entities = [e for e in extract_gold_entities_from_ann(ann_file) if e['label'] in ['Target', 'Element', 'Mineral']]
            
            gold_count += len(entities)
            for e in sorted(entities, key = lambda x: x['doc_end_char'] - x['doc_start_char'], reverse = True):
                inside = 0
                for begin, end in offset2entities:
                    if begin <= e['doc_start_char'] < e['doc_end_char'] <= end:
                        inside = 1
                        offset2entities[(begin, end)].append(e)
                if not inside:
                    offset2entities[(e['doc_start_char'], e['doc_end_char'])] = [e]
            for _, temp_entities in offset2entities.items():
                if len(temp_entities) > 1:
                    overlap_count += len(temp_entities)
                    single_count += 1
        print(f">>>Percentage of Nested Entities in {name} set:\n\n{gold_count} gold entities, with {overlap_count}({overlap_count/gold_count*100:.2f}%) of them are nested. These {overlap_count} nested entities could be reduced to {single_count} single entities ")






def load_files():
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
    
    dev_annfiles = [join(ann15_indir, file) for file in listdir(ann15_indir) if file.endswith(".ann")][42:]
    dev_textfiles = [join(ann15_indir, file.split(".ann")[0] + ".txt") for file in dev_annfiles]
    dev_corenlpfiles = [join(corenlp15_indir, file.split("/")[-1].split(".ann")[0] + ".txt.json") for file in dev_annfiles]
    assert all([exists(k) for k in dev_annfiles + dev_textfiles + dev_corenlpfiles])

    test_venues = ["lpsc16-C-raymond-sol1159-utf8", "mpf-reviewed+properties-v2", "phx-reviewed+properties-v2" ]

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
    return train_annfiles, train_textfiles, train_corenlpfiles, dev_annfiles, dev_textfiles, dev_corenlpfiles, test_annfiles, test_textfiles, test_corenlpfiles

def main():
    train_annfiles, train_textfiles, train_corenlpfiles, dev_annfiles, dev_textfiles, dev_corenlpfiles, test_annfiles, test_textfiles, test_corenlpfiles = load_files()

    # check percentage of gold nested entities 
    percentage_gold_nested_entities(train_annfiles, dev_annfiles ,test_annfiles)





    


# python make_train_val_test.py > ./stat/train_dev_test.txt
if __name__ == "__main__":
    main()


