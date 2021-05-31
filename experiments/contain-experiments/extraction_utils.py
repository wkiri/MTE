import copy, re, json, os, glob, warnings
from os.path import exists, join 


def make_tree_from_ann_file(text_file, ann_file):
    with open(text_file) as text_file, open(ann_file) as ann_file:
        texts = text_file.read()
        text_file.close()

        anns = map(lambda x: x.strip().split('\t'), ann_file)
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


def extract_entities_from_text(text_file, ann_file, doc = None, corenlp_file = None):
    """
    this function extracts entities from text file using a tree and doc
    Argument:
        text_file: text_file that contains the journal/abstract 
        
        ann_file: file that contains annotations from brat. 

        doc:  a dictionary that stores corenlp's parsing for text_file

        corenlp_file: is a file that stores corenlp's parsing for text_file

    """
    
    venue, year, docname, _ = get_docid(text_file)

    if doc is None and corenlp_file is None:
        raise NameError("Either doc_dict or corenlp_file must be provided ! ")
    if doc is None:
        # read corenlp file
        doc = json.load(open(corenlp_file, "r"))

    # note that if tree is built using system ners, then this function extracts system entities. make_tree_from_ann_file only builds tree over ann_file, which means that it builds tree over gold entities. 
    tree = make_tree_from_ann_file(text_file, ann_file)
    
    


    charoffset2label2entities = {}

    text = open(text_file, "r").read()

    for s in doc["sentences"]:
        tokens = [t for t in s["tokens"]]
        # correct_offset(tokens, text)

        sentid = int(s["index"]) # starts from 0 
        for tokidx, token in enumerate(tokens):
            token_begin, token_end = token["characterOffsetBegin"], token["characterOffsetEnd"]

            if text[token_begin: token_end] != token["word"]:
                warnings.warn(f"ERROR Mismatch text: ({token['word']})\n offset from corenlp: ({token['characterOffsetBegin']}, {token['characterOffsetEnd']})\ntext according to offset from corenlp: ({text[token_begin: token_end]})")
                print()
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
    
def get_docid(ann_file):
    venue = ann_file.split("/")[-2]
    if "lpsc" in ann_file:
        year = re.findall(r"lpsc(\d+)", ann_file)[0]
        docname = ann_file.split("/")[-1].split(".")[0]
    elif "mpf" in ann_file or "phx" in ann_file:
        year, docname = re.findall(r"(\d+)_(\d+)", ann_file.split("/")[-1])[0] 
    else:
        raise NameError(f"file must be from LPSC or MPF or PHX. Currently we have {ann_file}")
    doc_id = f"{venue}_{year}_{docname}"
    return venue, year, docname, doc_id

# def get_gold_annotid(ann_file):
def extract_gold_entities_from_ann(ann_file):
    venue, year, docname, _ = get_docid(ann_file)

    entities = []
    seen_annotids = set()
    with open(ann_file, "r") as f:
        for k in f.readlines():
            k = k.strip()
            if len(k.split("\t")) == 3:
                annot_id, label, span = k.split("\t")
                if annot_id in seen_annotids:
                    raise NameError(f"Duplicated Annotation IDs {annot_id} in {ann_file}")
                seen_annotids.add(annot_id)

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

def get_entity_id(entity):
    # this function gets a mention-level entity id 
    entity_id = f"{entity['venue']}, {entity['year']}, {entity['docname']}, {entity['doc_start_char']}, {entity['doc_end_char']}"
    return entity_id

def get_entity_coverage(entities, gold_entities):
    gold_ids = set([f"{e['doc_start_char']} {e['doc_end_char']} {e['venue']} {e['year']} {e['docname']}" for e in gold_entities])
    ids = set([f"{e['doc_start_char']} {e['doc_end_char']} {e['venue']} {e['year']} {e['docname']}" for e in entities])

    found_gold = len(ids.intersection(gold_ids))
    found_percent = found_gold/len(gold_ids)
    nonexisting_num = len(ids - gold_ids)
    nonexisting_percent = nonexisting_num / len(ids)

    print(f"{found_gold}/{len(gold_ids)}({found_percent*100:.2f}%) of gold entities are extracted from texts")
    print(f"There are {nonexisting_num}/{len(ids)}({nonexisting_percent*100:.2f}%) nonexisting entities extracted")


def extract_gold_relations_from_ann(ann_file):

    annotid_annotid_relation = []
    for annotation_line in open(ann_file).readlines():
        if annotation_line.strip() == "": continue
        splitline = annotation_line.strip().split('\t')
        annot_id = splitline[0]

        if splitline[0][0] == "R":
            args = splitline[1].split()
            if len(args) == 3:
                relation = args[0]
                arg1 = args[1].split(":")[1]
                arg2 = args[2].split(":")[1]
                annotid_annotid_relation.append((arg1, arg2, relation))

        elif splitline[0][0] == 'E': # event
            args         = splitline[1].split() 
            relation   = args[0].split(':')[0]
            
            anchor  = args[0].split(':')[1]
            args         = [a.split(':') for a in args[1:]]
            targets = [v for (t,v) in args if t.startswith('Targ')]
            cont    = [v for (t,v) in args if t.startswith('Cont')]

            for t in targets:
                for c in cont:
                    annotid_annotid_relation.append((t, c, relation))

    gold_entities = extract_gold_entities_from_ann(ann_file)
    annotid2entities = {e["annot_id"]: e for e in gold_entities}

    gold_relations = []
    for t, c, relation in annotid_annotid_relation:
        e1 = annotid2entities[t]
        e2 = annotid2entities[c]
        gold_relations.append((copy.deepcopy(e1), copy.deepcopy(e2), relation))

    return gold_relations

def extract_intrasent_goldrelations_from_ann(ann_file, corenlp_file = None, doc = None):
    # this function extracts gold relations with entities in the same sentence

    if doc is None and corenlp_file is None:
        raise NameError("Either doc_dict or corenlp_file must be provided ! ")
    if doc is None:
        # read corenlp file
        doc = json.load(open(corenlp_file, "r"))

    gold_relations = extract_gold_relations_from_ann(ann_file)

    offset2sentid = get_offset2sentid(doc = doc, corenlp_file = corenlp_file)

    intrasent_gold_relations = []
    for e1, e2, relation in gold_relations:
        sentid1 = get_sentid_from_offset(e1['doc_start_char'], e1['doc_end_char'], offset2sentid)
        sentid2 = get_sentid_from_offset(e2['doc_start_char'], e2['doc_end_char'], offset2sentid)

        if sentid1 is None or sentid2 is None: 
            continue 
        if sentid1 == sentid2:
            new_e1 = copy.deepcopy(e1)
            new_e2 = copy.deepcopy(e2)
            new_e1["sentid"] = sentid1
            new_e2["sentid"] = sentid2
            intrasent_gold_relations.append((new_e1, new_e2, relation))

    return intrasent_gold_relations

def get_offset2sentid(doc = None, corenlp_file = None):

    # get a dictonary of character offset to sentid

    if doc is None and corenlp_file is None:
        raise NameError("Either doc_dict or corenlp_file must be provided ! ")
    if doc is None:
        # read corenlp file
        doc = json.load(open(corenlp_file, "r"))

    offset2sentid = {}
    for sent in doc["sentences"]:
        offset = (sent["tokens"][0]["characterOffsetBegin"],  sent["tokens"][-1]["characterOffsetEnd"])
        sentid = int(sent["index"]) 

        assert offset not in offset2sentid
        offset2sentid[offset] = sentid
    return offset2sentid

def get_sentid_from_offset(doc_start_char, doc_end_char, offset2sentid):
    sentid = None
    for offset in offset2sentid:
        if offset[0] <= doc_start_char < doc_end_char <= offset[1]:
            return offset2sentid[offset]
    return sentid 

def extract_intrasent_entitypairs_from_text_file(text_file, ann_file, doc = None, corenlp_file = None):
    
    # this function extract all pairs of entities from the same sentence as relation candidates. note that here we would get duplicated entity pairs with reverse order, such as (t1, t2) and (t2, t1)
    """
    text_file: text_file that contains the journal/abstract 
        
        ann_file: file that contains annotations from brat. used to extract ners 

        doc:  a dictionary that stores corenlp's parsing for text_file

        corenlp_file: is a file that stores corenlp's parsing for text_file
    """

    if doc is None and corenlp_file is None:
        raise NameError("Either doc_dict or corenlp_file must be provided ! ")
    if doc is None:
        # read corenlp file
        doc = json.load(open(corenlp_file, "r"))

    entities = extract_entities_from_text(text_file, ann_file, doc = doc, corenlp_file = corenlp_file)

    # get all possible entity pairs. 
    intrasent_entitypairs = []
    for i in range(len(entities)):
        for j in range(len(entities)):
            if i == j: continue
            if entities[i]['sentid'] != entities[j]['sentid']:
                continue
            # note that a entity may be annotated with different labels, and so entities[i] and entities[j] may correspond to the same annotated text (e.g., Dillinger at (2505, 2514)  of lpsc15-C-raymond-sol1159-v3-utf8/2620.ann is labeled Target and Unit at the same time)
            intrasent_entitypairs.append((copy.deepcopy(entities[i]), copy.deepcopy(entities[j])))
    return intrasent_entitypairs


def get_relation_coverage(entitypairs, gold_relations):
    # this function calculates the coverage of gold relations in entitypairs
    gold_ids = set()
    for entity1, entity2, relation in gold_relations:
        entity1_id = get_entity_id(entity1)
        entity2_id = get_entity_id(entity2)
        gold_ids.add(f"{entity1_id},,{entity2_id}")

    ids = set()
    for entity1, entity2 in entitypairs:
        entity1_id = get_entity_id(entity1)
        entity2_id = get_entity_id(entity2)

        ids.add(f"{entity1_id},,{entity2_id}")

    found_num = len(ids.intersection(gold_ids))
    found_percent = found_num/len(gold_ids)

    print(f"{found_num}/{len(gold_ids)}({found_percent*100:.2f}%) of gold relations could be matched in entity pairs from texts")







if __name__ == "__main__":

    print("Warning: the statistics are reported over ann files which have at least 1 Target and 1 Component. Ann files that are not satisfying this constraint would not be taken into consideration. ")
    corenlp_dir = "../../parse/"

    gold_ids = set()
    ids = set()

    text_files = glob.glob("../../corpus-LPSC/lpsc15-C-raymond-sol1159-v3-utf8/*.txt")  \
                + glob.glob("../../corpus-LPSC/lpsc16-C-raymond-sol1159-utf8/*.txt") \
                # + glob.glob("../../corpus-LPSC/mpf-reviewed+properties-v2/*.txt")  \
                # + glob.glob("../../corpus-LPSC/phx-reviewed+properties-v2/*.txt")

    entities = []
    gold_entities = []
    gold_relations = []
    intrasent_goldrelations = []
    intrasent_entitypairs = []

    for text_file in text_files:

        ann_file = text_file.split(".txt")[0] + ".ann"
        corenlp_file = join(corenlp_dir.strip("/"), "/".join(text_file.split("/")[-2:]) + ".json")
        if not exists(corenlp_file):
            continue

        entities.extend(extract_entities_from_text(text_file, ann_file,corenlp_file = corenlp_file))
        gold_entities.extend(extract_gold_entities_from_ann(ann_file))
        gold_relations.extend(extract_gold_relations_from_ann(ann_file))

        intrasent_goldrelations.extend(extract_intrasent_goldrelations_from_ann(ann_file, corenlp_file = corenlp_file))
        intrasent_entitypairs.extend(extract_intrasent_entitypairs_from_text_file(text_file, ann_file, corenlp_file = corenlp_file))

    # check entity extraction 
    # get coverage
    get_entity_coverage(entities, gold_entities)
    task_entities = [e for e in entities if e['label'] in ['Target', 'Element', 'Mineral']]
    task_gold_entities = [e for e in gold_entities if e['label'] in ['Target', 'Element', 'Mineral']]
    # get task-specific entities coverage 
    get_entity_coverage(task_entities, task_gold_entities)


    task_intrasent_goldrelations = [(entity1,entity2, relation ) for entity1, entity2, relation in intrasent_goldrelations if entity1['label'] == 'Target' and entity2['label'] in ['Element', 'Mineral'] and relation == 'Contains']

    task_intrasent_entitypairs = [(entity1, entity2) for entity1, entity2 in intrasent_entitypairs if entity1['label'] == 'Target' and entity2['label'] in ['Element', 'Mineral']]

    # check relation extraction
    get_relation_coverage(task_intrasent_entitypairs, task_intrasent_goldrelations) 


