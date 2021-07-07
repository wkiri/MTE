from extraction_utils import  extract_gold_relations_from_ann, get_sentid_from_offset, get_offset2sentid, get_offset2docidx, get_docidx_from_offset
from os.path import join, abspath, exists
import json, numpy as np, sys, glob, os 


def create_bins(items, bins):
    counts = {}
    for i in range(1, len(bins)):
        assert bins[i-1] < bins[i]
        counts[(bins[i-1], bins[i])] = 0 
    counts[(bins[-1], sys.maxsize)] = 0 # for items that are larger in the max value in bins

    for i in items:
        for (b1, b2) in counts:
            if b1 <= i < b2: 
                counts[(b1, b2)] += 1
    return counts

def print_bincounts(bincounts):
    totcount = sum([count for _, count in bincounts.items()])
    
    print(bincounts)
    for (b1, b2) in sorted(bincounts.keys(), key = lambda x: x[0]):
        count = bincounts[(b1,b2)]
        if b2 == sys.maxsize:
            b2 = "INF"
        print(f"     range({b1}, {b2}): {count} ({count/totcount*100:.2f})\n")




def distance(ann_files, corenlp_files):

    diff_sents = [] # sentence-level distance between two entities 
    diff_toks = [] # token-level distance between two entities
    for ann_file, corenlp_file in zip(ann_files, corenlp_files):
        relations = [ (e1, e2, relation)  for e1, e2, relation in extract_gold_relations_from_ann(ann_file, use_component = True) if relation == 'Contains' and e1['label'] == 'Target' and e2['label'] == 'Component']

        offset2sentid = get_offset2sentid(corenlp_file = corenlp_file)
        offset2docidx = get_offset2docidx(corenlp_file = corenlp_file)

        
        for e1, e2, relation in relations:
            sid1 = get_sentid_from_offset(e1['doc_start_char'], e1['doc_end_char'], offset2sentid)
            sid2 = get_sentid_from_offset(e2['doc_start_char'], e2['doc_end_char'], offset2sentid)
            diff_sents.append(abs(sid2 - sid1))

            tbegin1, tend1 = get_docidx_from_offset(e1['doc_start_char'], e1['doc_end_char'], offset2docidx)
            tbegin2, tend2 = get_docidx_from_offset(e2['doc_start_char'], e2['doc_end_char'], offset2docidx)

            tok_dist = sys.maxsize
            for idx1 in [tbegin1, tend1]:
                for idx2 in [tbegin2, tend2]:
                    # print(tok_dist, abs(idx1 - idx2))
                    tok_dist = min(tok_dist, abs(idx1 - idx2))
            diff_toks.append(tok_dist)

    print("sentence-level distance between Target and Component")
    print_bincounts(create_bins(diff_sents, [0,1,2,3,4,5,8, 10]))
    print("token-level distance between Target and Component")
    print_bincounts(create_bins(diff_toks, [0, 50, 100, 200, 300, 400, 500]))

def relations(ann_files, corenlp_files):
    count = 0 
    for ann_file, corenlp_file in zip(ann_files, corenlp_files):
        rels = [ (e1, e2, relation)  for e1, e2, relation in extract_gold_relations_from_ann(ann_file, use_component = True) if relation == 'Contains' and e1['label'] == 'Target' and e2['label'] == 'Component']

        count += len(rels)
    print(f"Count Contains Relations: {count}")


def order(ann_files, corenlp_files):

    order = {'xsent':
                {'L2R':0, 'R2L':0}, 
            'insent':
                {'L2R':0, 'R2L':0}
            }
    for ann_file, corenlp_file in zip(ann_files, corenlp_files):
        relations = [ (e1, e2, relation)  for e1, e2, relation in extract_gold_relations_from_ann(ann_file, use_component = True) if relation == 'Contains' and e1['label'] == 'Target' and e2['label'] == 'Component']

        offset2sentid = get_offset2sentid(corenlp_file = corenlp_file)
        offset2docidx = get_offset2docidx(corenlp_file = corenlp_file)

        
        for e1, e2, relation in relations:
            sid1 = get_sentid_from_offset(e1['doc_start_char'], e1['doc_end_char'], offset2sentid)
            sid2 = get_sentid_from_offset(e2['doc_start_char'], e2['doc_end_char'], offset2sentid)

            direction = 'L2R' if e1['doc_start_char'] < e2['doc_start_char'] else 'R2L'

            if sid1 == sid2:
                order['insent'][direction] += 1
            else:
                order['xsent'][direction] += 1

    print("Order between Target and Component")
    print(f"      Cross-sentence order: {order['xsent']['L2R']} ({order['xsent']['L2R']/(order['xsent']['L2R'] + order['xsent']['R2L'])*100:2f}) L2R, {order['xsent']['R2L']} ({order['xsent']['R2L']/(order['xsent']['L2R'] + order['xsent']['R2L'])*100:2f}) R2L")
    print(f"      In-sentence order   : {order['insent']['L2R']} ({order['insent']['L2R']/(order['insent']['L2R'] + order['insent']['R2L'])*100:2f}) L2R, {order['insent']['R2L']} ({order['insent']['R2L']/(order['insent']['L2R'] + order['insent']['R2L'])*100:2f}) R2L")

    # total stats regardless of sentence boundary
    L2R = order['insent']['L2R'] + order['xsent']['L2R']
    R2L = order['insent']['R2L'] + order['xsent']['R2L']

    print(f"      Total: {L2R} ({L2R/(L2R+R2L) * 100:.2f}) L2R, {R2L} ({R2L/(L2R+R2L) * 100:.2f}) R2L ")

def sentences(ann_files, corenlp_files):

    # avg of sentences in a doc 
    sents = [] 
    for ann_file, corenlp_file in zip(ann_files, corenlp_files):
        doc = json.load(open(corenlp_file))
        sents.append(len(doc['sentences']))
    print(f"Number of sentences: AVG {np.mean(sents):.2f}, MAX {max(sents):.2f}, MIN {min(sents):.2f}")

def analyze_order(ann_files, corenlp_files, analyze_dir = './temp'):
    # analyze cases of cross-sentene relation with component preceding target
    if not exists(analyze_dir):
        os.makedirs(analyze_dir)

    preceding_tarf = open(join(analyze_dir, 'preceding_target.txt'), 'w')
    preceding_compf = open(join(analyze_dir, 'preceding_component.txt'), 'w')

    for ann_file, corenlp_file in zip(ann_files, corenlp_files):
        doc = json.load(open(corenlp_file))
        for e1, e2, relation in extract_gold_relations_from_ann(ann_file, use_component = True):
            if not (relation == 'Contains' and e1['label'] == 'Target' and e2['label'] == 'Component'):
                continue
            offset2sentid = get_offset2sentid(corenlp_file = corenlp_file)
            sid1 = get_sentid_from_offset(e1['doc_start_char'], e1['doc_end_char'], offset2sentid)
            sid2 = get_sentid_from_offset(e2['doc_start_char'], e2['doc_end_char'], offset2sentid)
        
            if sid1 == sid2: continue


            title = f"\n\n{e1['venue']}, {e1['year']}, {e1['docname']}"
            entity_line = f"{e1['text']}, {e2['text']}"
            if sid1 > sid2: 
                sents = "\n".join([ " ".join([tok['word'] for tok in doc['sentences'][i]['tokens']]) for i in range(sid2, sid1+1)]) + "\n"

                preceding_compf.write('\n'.join([title, entity_line, sents]))
            else:
                sents = "\n".join([ " ".join([tok['word'] for tok in doc['sentences'][i]['tokens']]) for i in range(sid1, sid2+1)]) + "\n"

                preceding_tarf.write('\n'.join([title, entity_line, sents]))
    preceding_tarf.close()
    preceding_compf.close()






if __name__ == "__main__":

    inputdirs = [
    "../../corpus-LPSC/lpsc15-C-raymond-sol1159-v3-utf8", 
    "../../corpus-LPSC/lpsc16-C-raymond-sol1159-utf8/", 
    "../../corpus-LPSC/mpf-reviewed+properties-v2/", 
    "../../corpus-LPSC/phx-reviewed+properties-v2/"
    ]
    corenlp_dir = "../../parse/"


    text_files = [] 

    for inputdir in inputdirs:
        text_files.extend(glob.glob(join(inputdir, "*.txt")))

    corenlp_files = [] 
    ann_files = [] 
    for text_file in text_files:

        ann_file = text_file.split(".txt")[0] + ".ann"
        corenlp_file = join(corenlp_dir.strip("/"), "/".join(text_file.split("/")[-2:]) + ".json")
        if not exists(corenlp_file):
            continue

        ann_files.append(ann_file)
        corenlp_files.append(corenlp_file)
    relations(ann_files, corenlp_files)
    distance(ann_files, corenlp_files)
    order(ann_files, corenlp_files)
    sentences(ann_files, corenlp_files)


    analyze_order([f for f in ann_files if 'lpsc15-C-raymond-sol1159-v3-utf8' in f], [f for f in corenlp_files if 'lpsc15-C-raymond-sol1159-v3-utf8' in f])
