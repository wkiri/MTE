import argparse, sys, os, json, io, pickle
from os.path import join, dirname, abspath, exists
# curpath = dirname(abspath(__file__))
curpath = abspath(".")
parentpath = dirname(curpath)
sys.path.append(parentpath)

datapath = join(dirname(dirname(dirname(curpath))), 'corpus-LPSC')
from my_name_utils import canonical_elemin_name, canonical_target_name
from extraction_utils import extract_gold_entities_from_ann

from instance import Span_Instance

def load_test_entities(testlist):
    lines = [ line for line in open(testlist, 'r').read().strip().split('\n') if line.strip() != '']

    ann_files = [] 
    for line in lines:
        text_file, ann_file = line.split(',')
        ann_file = join(datapath, '/'.join(ann_file.split('/')[-2:]))
        ann_files.append(ann_file)
    entities = [] 
    for i, ann_file in enumerate(ann_files):
        sys.stdout.write(f'\r reading {i}/{len(ann_files)} files')
        sys.stdout.flush()
        for e in extract_gold_entities_from_ann(ann_file):
            if e['label'] not in ['Target', 'Mineral', 'Element']:
                continue
            entities.append(Span_Instance(e['venue'], e['year'], e['docname'], e['doc_start_char'], e['doc_end_char'], e['text'], e['label']))
    return entities



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="make test entity instances ")
    parser.add_argument("--testlist", help="test list", required=True)

    parser.add_argument("--outfile", help="""outfile to store test entities""", default = 'data/test.eval.entities')
    args = parser.parse_args()

    testlist = args.testlist 
    entities = load_test_entities(testlist)
    print(f'\nExtracted {len(entities)} entities ')
    print(f'Saving to {args.outfile}')
    with open(args.outfile, 'wb') as f:
        pickle.dump(entities, f)