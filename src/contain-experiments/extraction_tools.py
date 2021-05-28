import copy, re, json, os, glob, warnings
from os.path import exists, join 


def make_tree_from_annfile(text_file, annfile):
    with open(text_file) as text_file, open(annfile) as annfile:
        texts = text_file.read()
        text_file.close()

        anns = map(lambda x: x.strip().split('\t'), annfile)
        anns = filter(lambda x: len(x) > 2, anns)
        # FIXME: ignoring the annotatiosn which are complex

        anns = filter(lambda x: ';' not in x[1], anns)
        # FIXME: some annotations' spread have been split into many, separated by ; ignoring them

        def __parse_ann(ann):
            spec = ann[1].split()
            name = spec[0]
            markers = list(map(lambda x: int(x), spec[1:]))
            #t = ' '.join([texts[begin:end] for begin,end in zip(markers[::2], markers[1::2])])
            t = texts[markers[0]:markers[1]]
            if not t == ann[2]:
                print("Error: Annotation mis-match, file=%s, ann=%s" % (text_file, str(ann)))
                return None
            return (name, markers, t)
        anns = map(__parse_ann, anns) # format
        anns = filter(lambda x: x, anns) # skip None

        # building a tree index for easy accessing
        tree = {}
        for entity_type, pos, name in anns:
            begin, end = pos[0], pos[1]
            if begin not in tree:
                tree[begin] = {}
            node = tree[begin]
            if end not in node:
                node[end] = []
            node[end].append(entity_type)

        return tree


def collect_entity_at_offset(token, sentid, tokidx, charoffset, offset_entity_label, charoffset2label2entities):
        # if charoffset2entities is emtpy, create an entity 

        if charoffset not in charoffset2label2entities:
            charoffset2label2entities[charoffset] = {}
        if offset_entity_label not in  charoffset2label2entities[charoffset]:
            charoffset2label2entities[charoffset][offset_entity_label] = []

        entity = {
            "text": token["word"],
            "doc_start_char": token["characterOffsetBegin"],
            "doc_end_char": token["characterOffsetEnd"],
            "sent_start_idx": int(tokidx),
            "sent_end_idx": int(tokidx) + 1,
            "sentid": int(sentid)
        }
        charoffset2label2entities[charoffset][offset_entity_label].append(entity)

def merge_and_make_entities(charoffset2label2entities, text_file):
    entities = []
    for charoffset in charoffset2label2entities:
        for label in charoffset2label2entities[charoffset]:
            entity_parts = sorted(charoffset2label2entities[charoffset][label], key = lambda x: x["sent_start_idx"])

            # merge while make sure entity parts are sequential and do not have overlap 
            entity = copy.deepcopy(entity_parts[0])
            last_entity_is_hypen_or_underscore = 0
            for i in range(1, len(entity_parts)):
                curentity = entity_parts[i]
                        

                if not (charoffset[0] <= entity["doc_start_char"] < entity["doc_end_char"] <= curentity["doc_start_char"] < curentity["doc_end_char"] <= charoffset[1]):

                    raise NameError(f"Entity parts are not able to form a valid entity due to incorrect boundaries to merge in {text_file}:\n OFFSET: {charoffset}\n   last entity part: {entity['doc_start_char']}, {entity['doc_end_char']}, {entity['text']}\n   cur entity part:  {curentity['doc_start_char']}, {curentity['doc_end_char']}, {curentity['text']}")
                if curentity['sentid'] != entity['sentid']:
                    raise NameError(f"Inconsistent sentence ID in {text_file}! last entity: {entity['sentid']}, current entity: {curentity['sentid']}")
                # merge 
                text = entity['text']
                if curentity['text'] in ["_", "-"]: # if current word is a hyphen or underscore, then append it to the text without any space 
                    text = entity['text'] + curentity['text']
                    last_entity_is_hypen_or_underscore = 1
                else: # if current word is not a hypen but last word is hypen, then we append it to the text without spance 
                    if last_entity_is_hypen_or_underscore:
                        text = entity['text'] + curentity['text']
                    else:
                        text = entity['text'] + " " + curentity['text'] 
                    last_entity_is_hypen_or_underscore = 0 


                entity = {
                    "text": text,
                    "doc_start_char": entity['doc_start_char'],
                    "doc_end_char": curentity['doc_end_char'],
                    "sent_start_idx": entity['sent_start_idx'],
                    "sent_end_idx": curentity['sent_end_idx'],
                    "sentid": entity['sentid']
                }
            entity['label'] = label 
            entities.append(entity)
    return entities


def extract_entities_from_text(text_file, tree,doc = None, corenlp_file = None):
    # corenlp_file is a file that stores corenlp's parsing for text_file

    # doc_dict is a dictionary that stores corenlp's parsing for text_file
    venue, year, docname, _ = get_docid(text_file)

    if doc is None and corenlp_file is None:
        raise NameError("Either doc_dict or corenlp_file must be provided ! ")
    if doc is None:
        # read corenlp file
        doc = json.load(open(corenlp_file, "r"))

    # this function extracts entities from text file using a tree and doc_dict

    # tree is a dict, check for details in make_tree_from_annfile 
    # a doc_dict is the json object produced by using stanford corenlp to parse the text file 

    # note that if tree is built using system ners, then this function extracts system entities 


    charoffset2label2entities = {}

    text = open(text_file, "r").read()

    for s in doc["sentences"]:
        tokens = [t for t in s["tokens"]]
        # correct_offset(tokens, text)

        sentid = int(s["index"]) # starts from 0 
        for tokidx, token in enumerate(tokens):
            token_begin, token_end = token["characterOffsetBegin"], token["characterOffsetEnd"]

            if text[token_begin: token_end] != token["word"]:
                warnings.warn(f"ERROR Mismatch text: {token['word']}\n offset from corenlp: {token['characterOffsetBegin']}, {token['characterOffsetEnd']}\ntext according to offset from corenlp: {text[token_begin: token_end]}")
                continue

            for begin in tree:
                for end in tree[begin]:
                    if  begin <= token_begin < token_end <= end:

                        charoffset = (begin ,end)

                        for offset_entity_label in tree[begin][end]:
                            collect_entity_at_offset(token, sentid, tokidx, charoffset, offset_entity_label, charoffset2label2entities)

    entities = merge_and_make_entities(charoffset2label2entities, text_file)
    for e in entities:
        e["venue"] = venue
        e["docname"] = docname
        e["year"] = year 
    
    return entities
    
def get_docid(annfile):
    venue = annfile.split("/")[-2]
    if "lpsc" in annfile:
        year = re.findall(r"lpsc(\d+)", annfile)[0]
        docname = annfile.split("/")[-1].split(".txt")[0]
    elif "mpf" in annfile or "phx" in annfile:
        year, docname = re.findall(r"(\d+)_(\d+)", annfile.split("/")[-1])[0] 
    else:
        raise NameError(f"file must be from LPSC or MPF or PHX. Currently we have {annfile}")
    doc_id = f"{venue}_{year}_{docname}"
    return venue, year, docname, doc_id



# def get_gold_annotid(annfile):
def extract_gold_entities_from_ann(annfile):
    venue, year, docname, _ = get_docid(annfile)

    # only get allowed ner types 
    entities = []
    seen_annotids = set()
    with open(annfile, "r") as f:
        for k in f.readlines():
            k = k.strip()
            if len(k.split("\t")) == 3:
                annot_id, label, span = k.split("\t")
                if annot_id in seen_annotids:
                    raise NameError(f"Duplicated Annotation IDs {annot_id} in {annfile}")

                label, doc_start_char, doc_end_char = label.split()
                doc_start_char = int(doc_start_char)
                doc_end_char = int(doc_end_char)
                if annot_id[0] == "T":
                    entity = {
                        "text": span.lower(),
                        "annot_id": annot_id,
                        "doc_start_char": doc_start_char,
                        "doc_end_char": doc_end_char,
                        "label": label,
                        "venue": venue,
                        "year": year,
                        "docname": docname 
                    }
                    entities.append(entity)
    return entities

if __name__ == "__main__":

# NameError: Entity parts are not able to form a valid entity due to incorrect boundaries to merge in ../data/corpus-LPSC/mpf-reviewed+properties-v2/2015_2572.txt:
#  OFFSET: (2157, 2165)

    text_file = "../data/corpus-LPSC/mpf-reviewed+properties-v2/2020_2668.txt"
    annfile = text_file.split(".txt")[0] + ".ann"
    corenlp_dir = "../data/stanford-parse/corpus-LPSC/"
    corenlp_file = join(corenlp_dir, "/".join(text_file.split("/")[-2:]) + ".json")
    tree = make_tree_from_annfile(text_file, annfile)
    text = open(text_file, "r").read()

    gold_ids = set()
    ids = set()
    for text_file in glob.glob("../data/corpus-LPSC/*/*.txt"):

        venue, year, docname, _ = get_docid(text_file)
        annfile = text_file.split(".txt")[0] + ".ann"
        corenlp_file = join(corenlp_dir.strip("/"), "/".join(text_file.split("/")[-2:]) + ".json")
        if not exists(corenlp_file):
            continue
        tree =make_tree_from_annfile(text_file, annfile)
        entities = extract_entities_from_text(text_file, tree,corenlp_file = corenlp_file)
        gold_entities = extract_gold_entities_from_ann(annfile)
        for e in gold_entities:
            gold_ids.add(f"{e['doc_start_char']} {e['doc_end_char']} {venue} {year} {docname}")
        for e in entities:
            ids.add(f"{e['doc_start_char']} {e['doc_end_char']} {venue} {year} {docname}")
    # get coverage
    entities = [e for e in entities if e['label'] in ['Target', 'Element', 'Mineral']]
    gold_entities = [e for e in gold_entities if e['label'] in ['Target', 'Element', 'Mineral']]
    print(len(ids.intersection(gold_ids))/len(gold_ids))

