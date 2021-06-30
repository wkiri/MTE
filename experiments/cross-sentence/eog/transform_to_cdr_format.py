# make data into a file that matches the format of cdr (https://github.com/JHnlp/BioCreative-V-CDR-Corpus)

import sys, os, re, argparse, json
from os.path import abspath, dirname, exists, join
from os import listdir 
curpath = dirname(abspath(__file__))
upperpath = dirname(curpath)
sys.path.append(upperpath)
from extraction_utils import extract_gold_relations_from_ann,extract_entities_from_text

from my_name_utils import canonical_target_name, canonical_elemin_name

def get_name_identifier(name, ner_type):
    if ner_type == 'Target':
        new_name = canonical_target_name(name)
    else:
        assert ner_type in ['Element', 'Component', 'Mineral']
        new_name = canonical_elemin_name(name)
    identifier = ''.join(new_name.split())
    return identifier

def get_doc_in_cdr_format(ann_file, text_file, corenlp_file, use_component = True):

    # PMID<tab>START OFFSET<tab>END OFFSET<tab>text MENTION<tab>mention TYPE (e.g. Disease)<tab>database IDENTIFIER<tab>Individual mentions

    # NOTE: docs without either target or component would be filtered out 
    docid = None
    entity_section = [] 
    has_target = 0 
    has_component = 0 
    doc = json.load(open(corenlp_file,"r"))
    seen_entity = set()
    for e in extract_entities_from_text(text_file, ann_file, corenlp_file = corenlp_file, use_component = use_component):
        if e['label'] not in ['Target','Element','Mineral','Component']:
            continue
        if e['label'] == 'Target':
            has_target = 1
        else:
            has_component = 1

        if docid is None:
            docid = f"{e['venue']}:{e['year']}:{e['docname']}"
        assert docid is not None
        entity_name = get_name_identifier(e['text'], e['label'])

        start_char = e['doc_start_char']
        end_char = e['doc_end_char']
        entity_section.append(f"{docid}\t{start_char}\t{end_char}\t{e['text']}\t{e['label']}\t{entity_name}")

        seen_entity.add(f"{e['venue']}:{e['year']}:{e['docname']}:{e['doc_start_char']}:{e['doc_end_char']}:{e['text']}".lower())
    if not (has_target and has_component):
        return None
    title_line = f"{docid}|t|." # create a fake title "." in order to fit the format
    text = open(text_file, "r").read()
    if text[0] == ' ':
        text = "'" + text[1:]
    text_line = f"{docid}|a|{text}"
    # senttok_line = f"{docid}<linesep>"+"<sentsep>".join(["<wordsep>".join([tok['word'] for tok in sent['tokens']]) for sent in doc['sentences']])

    relation_section = []
    relation_count = 0
    unique_relations = set() 
    for e1, e2, relation in extract_gold_relations_from_ann(ann_file, use_component = use_component):
        if not (e1['label'] == 'Target' and e2['label'] in ['Component', 'Element', 'Mineral'] and relation == 'Contains'):
            continue
        # only keep relations of which entities could be extracted 

        e1_extracted = f"{e1['venue']}:{e1['year']}:{e1['docname']}:{e1['doc_start_char']}:{e1['doc_end_char']}:{e1['text']}".lower() in seen_entity
        e2_extracted = f"{e2['venue']}:{e2['year']}:{e2['docname']}:{e2['doc_start_char']}:{e2['doc_end_char']}:{e2['text']}".lower() in seen_entity
        if not (e1_extracted and e2_extracted):
            continue

        id1 = get_name_identifier(e1['text'], e1['label'])
        id2 = get_name_identifier(e2['text'], e2['label'])
        relation_count += 1
        relation_section.append(f"{docid}\tContains\t{id1}\t{id2}")
        unique_relations.add((id1, id2))

    return "\n".join([title_line, text_line, f"{docid}|<corenlpfile>:"+corenlp_file, '\n'.join(entity_section),'\n'.join(relation_section) + '\n']), relation_count, len(unique_relations)

def make_data_in_cdr_format(ann_files, text_files, corenlp_files, use_component, outfile):
    docs = []
    relation_count = 0 
    unique_relation_count = 0 
    for ann_file, text_file, corenlp_file in zip(ann_files, text_files, corenlp_files):
        ret = get_doc_in_cdr_format(ann_file, text_file, corenlp_file, use_component = use_component)
        if ret is not None:
            doc_str, temp_relation_count, temp_unique_relation_count = ret 
            relation_count += temp_relation_count
            unique_relation_count += temp_unique_relation_count
            docs.append(doc_str)
    print(f"Collected {len(docs)} docs, {relation_count} relations, {unique_relation_count} unique relations")
    docs = "\n".join(docs)
    print(f"Saving to {outfile}")
    with open(outfile, "w") as f:
        f.write(docs)

def main(args):
    use_component = args.use_component

    proj_path = dirname(dirname(dirname(curpath)))
    datadir_prefix = join(proj_path, "corpus-LPSC")
    parse_prefix = join(proj_path, 'parse')

    # ---- make training samples ----
    print(" ----- making training samples ... ")
    ann15_indir = join(datadir_prefix, "lpsc15-C-raymond-sol1159-v3-utf8")
    train_annfiles = [join(ann15_indir, file) for file in listdir(ann15_indir) if file.endswith(".ann")][:42]
    train_textfiles = [join(ann15_indir, file.split(".ann")[0] + ".txt") for file in train_annfiles]
    train_corenlps = [join(parse_prefix, file.split("/")[-2], file.split("/")[-1] + ".json") for file in train_textfiles]

    assert all([exists(k) for k in train_annfiles + train_textfiles + train_corenlps])
    print("> Making Training data")
    if not exists('./data/mars'):
        os.makedirs('./data/mars')
    outfile = "./data/mars/train.txt"
    make_data_in_cdr_format(train_annfiles, train_textfiles, train_corenlps, use_component, outfile)

    # ---- make val samples ----
  
    dev_annfiles = [join(ann15_indir, file) for file in listdir(ann15_indir) if file.endswith(".ann")][42:]
    dev_textfiles = [join(ann15_indir, file.split(".ann")[0] + ".txt") for file in dev_annfiles]
    dev_corenlps = [join(parse_prefix, file.split("/")[-2], file.split("/")[-1] + ".json") for file in dev_textfiles]

    assert all([exists(k) for k in dev_annfiles + dev_textfiles + dev_corenlps])
    outfile = './data/mars/dev.txt'
    make_data_in_cdr_format(dev_annfiles, dev_textfiles, dev_corenlps, use_component, outfile)

    # -------- make test samples ---------
    test_venues = ['lpsc16-C-raymond-sol1159-utf8', 'mpf-reviewed+properties-v2','phx-reviewed+properties-v2']
    
    test_annfiles = []
    test_textfiles = []
    for venue in test_venues:
        ann_files =[join(datadir_prefix, venue, file) for file in listdir(join(datadir_prefix, venue)) if file.endswith(".ann")]

        text_files = [file.split(".ann")[0] + ".txt" for file in ann_files]

        test_annfiles.extend(ann_files)
        test_textfiles.extend(text_files)
    test_corenlps = [join(parse_prefix, file.split("/")[-2], file.split("/")[-1] + ".json") for file in test_textfiles]

    assert all([exists(k) for k in test_annfiles + test_textfiles + test_corenlps])
    outfile = './data/mars/test.txt'
    make_data_in_cdr_format(test_annfiles, test_textfiles,test_corenlps, use_component, outfile)

    # print("> Making Test data using gold ners")
    # outfile = "./data/mars/test.txt"
    # outfile = "./data/test/sys_ner/docs.json"
    # outfile = "./data/test/gold_relins.pkl"
    # extract_gold_data(test_annfiles, test_textfiles, test_corenlpfiles, outfile, use_component)

if __name__ == "__main__":
    print("NOTE THAT the relations are extracted only from entities that could be extracted from text files ")
    parser = argparse.ArgumentParser()
    parser.add_argument("--use_component", type = int, choices = [0,1], required = True)

    args = parser.parse_args()
    main(args)
 




