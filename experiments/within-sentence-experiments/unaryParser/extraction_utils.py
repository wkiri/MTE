# python3
# extraction_utils.py
# Mars Target Encyclopedia
# This script contains codes to extract entities from text files and annotations from ann files. 
#
# Yuan Zhuang
# July 30, 2021
# Copyright notice at bottom of file.

import copy, re, json, os, glob, warnings, sys
from os.path import exists, join, abspath, dirname
from copy import deepcopy 

from name_utils import targettab,symtab, canonical_name, canonical_target_name, canonical_property_name

def canonical_component_name(name):
    """
    This function gets canonical name for a component (either element/mineral): 
    """
    # remove hypen, unserscore, and extra space 
    name = " ".join(re.sub(r"[-_]", " ",name).split())
    name = " ".join([canonical_name(k) for k in name.split()])
    return name

def add_entities(queue, e):
    # add entities and merge entities if possible. Merge entities when two words have the same ner label that is not 'O' and (adjacent or two words are separated by hyphens or underscores). Note that this method is not perfect since we always merge adjacent words with the same NER into an entity, thus will lose a lot of smaller entities. For example, we will get only "Iron - Feldspar" and miss "Iron" and "Feldspar"

    if not len(queue) or e['label'] == 'O':
        queue.append(deepcopy(e))
        return 
    last_e = queue[-1]
    if last_e['label'] == e['label']:
        # merge 
        last_e['text'] = f"{last_e['text']} {e['text']}"
        last_e['doc_end_char'] = e['doc_end_char']
        last_e['sent_end_idx'] = e['sent_end_idx']
    else:
        if len(queue) > 1 and queue[-1]['text'] in ["_", "-"] and queue[-2]['label'] == e['label']: # words that are splitted by hyphen or underscores
            queue[-2]['text'] = f"{queue[-2]['text']}{last_e['text']}{e['text']}"
            queue[-2]['doc_end_char'] = e['doc_end_char']
            queue[-2]['sent_end_idx'] = e['sent_end_idx']
            queue.pop(-1)
        else:
            queue.append(deepcopy(e))

def extract_system_entities(doc = None, corenlp_file = None, use_component = False):
    """ extract system ners """
    """
    Args:
        doc: 
            output dictionary of CoreNLP
        
        corenlp_file: 
            a file that stores the output dictionary of CoreNLP 
        
        use_component:
            a boolean indicating whether the label of a Element/Mineral entity should be changed to Component 
    """

    # if use_component is True, do two passes of extraction. the first keeps 'Element' and 'Mineral' and merge. The second pass changes 'Element' and 'Mineral' to 'Component' and then merge them. then for all entities we get, we change the entities collected in both passes to component   

    if doc is None and corenlp_file is None:
        raise NameError("Both doc and corenlp_file is None! ")
    if doc is None:
        # read corenlp file
        doc = json.load(open(corenlp_file, "r"))

    has_ner_entry = "ner" in doc["sentences"][0]["tokens"][0]

    if not has_ner_entry:
        raise NameError("doc or corenlp_file must contain NER predictions!")

    entities = []
    for sent in doc['sentences']:
        sentid = int(sent["index"])
        sent_entities = []
        for tokidx, token in enumerate(sent['tokens']):
            entity = {
            "text": token["word"],
            "doc_start_char": token["characterOffsetBegin"],
            "doc_end_char": token["characterOffsetEnd"],
            "sent_start_idx": int(tokidx),
            "sent_end_idx": int(tokidx) + 1,
            "sentid": int(sentid),
            "label": token['ner']
            }
            add_entities(sent_entities, entity)
        if use_component:
            for e in sent_entities:
                if e['label'] in ['Element', 'Mineral']:
                    e['label'] = 'Component'

            new_sent_entities = []
            for tokidx, token in enumerate(sent['tokens']):
                entity = {
                "text": token["word"],
                "doc_start_char": token["characterOffsetBegin"],
                "doc_end_char": token["characterOffsetEnd"],
                "sent_start_idx": int(tokidx),
                "sent_end_idx": int(tokidx) + 1,
                "sentid": int(sentid),
                "label": 'Component' if token['ner'] in ['Element', 'Mineral'] else token['ner'] 
                }
                add_entities(new_sent_entities, entity)

            new_sent_entities = new_sent_entities + sent_entities
            sent_entities = []

            # remove duplicate entities generated in two passes
            seen_id = set()
            for e in new_sent_entities:
                entity_id = f"{e['doc_start_char']} {e['doc_end_char']}"
                if entity_id not in seen_id:
                    sent_entities.append(e)
                    seen_id.add(entity_id)

        entities.extend([e for e in sent_entities if e['label'] != 'O'])
    for e in entities:
        if e['label'] == 'Target':
            e['std_text'] = canonical_target_name(e['text'])
        elif e['label'] in ['Element', 'Mineral', 'Component']:
            e['std_text'] = canonical_component_name(e['text'])

    

    return entities





def make_tree_from_ann_file(text_file, ann_file, be_quiet = True):
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
                if not be_quiet:
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
        """ map character offset to label to entities """

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
            entity = deepcopy(entity_parts[0])
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


def extract_entities_from_text(text_file, ann_file, doc = None, corenlp_file = None, use_component = False, be_quiet = True, use_sys_ners = False):
    """
    this function extracts entities from text file 
    Argument:
        text_file: text_file that contains the journal/abstract 
        
        ann_file: file that contains annotations from brat. 

        doc:  a dictionary that stores corenlp's parsing for text_file. either doc or corenlp_file must not be none. 

        corenlp_file: a file that stores corenlp's parsing for text_file. If use_sys_ners is True, then corenlp_file must point to the parse results (in json file) which store the system ner predictons

        use_component: whether to map element and mineral to component 
    
        be_quiet: whether to print out warnings during extraction

        use_sys_ners: whether extract system entities

    """
    
    venue, year, docname, _ = get_docid(text_file)

    if doc is None and corenlp_file is None:
        raise NameError("Either doc_dict or corenlp_file must be provided ! ")
    if doc is None:
        # read corenlp file
        doc = json.load(open(corenlp_file, "r"))

    # note that if tree is built using system ners, then this function extracts system entities. make_tree_from_ann_file only builds tree over ann_file, which means that it builds tree over gold entities. 
    if use_sys_ners:
        entities = extract_system_entities(doc = doc, use_component = use_component)
    else:
        tree = make_tree_from_ann_file(text_file, ann_file)
    
        charoffset2label2entities = {}

        text = open(text_file, "r").read()

        for s in doc["sentences"]:
            tokens = [t for t in s["tokens"]]
            sentid = int(s["index"]) # starts from 0 
            for tokidx, token in enumerate(tokens):
                token_begin, token_end = token["characterOffsetBegin"], token["characterOffsetEnd"]

                if text[token_begin: token_end] != token["word"]:
                    if not be_quiet:
                        warnings.warn(f"ERROR Mismatch text: ({token['word']})\n offset from corenlp: ({token['characterOffsetBegin']}, {token['characterOffsetEnd']})\ntext according to offset from corenlp: ({text[token_begin: token_end]})")
                    continue

                for begin in tree:
                    for end in tree[begin]:
                        if  begin <= token_begin < token_end <= end:

                            charoffset = (begin ,end)

                            for offset_entity_label in tree[begin][end]:
                                collect_entity_at_offset(token, sentid, tokidx, charoffset, offset_entity_label, charoffset2label2entities)
        
        entities = merge_and_make_entities(charoffset2label2entities, text_file)

        if use_component:
            for e in entities:
                if e['label'] in ['Element', 'Mineral']:
                    e['label'] = 'Component'
    for e in entities:
        e["venue"] = venue
        e["docname"] = docname
        e["year"] = year 

        if e['label'] == 'Target':
            e['std_text'] = canonical_target_name(e['text'])
        elif e['label'] in ['Element', 'Mineral', 'Component']:
            e['std_text'] = canonical_component_name(e['text'])

    
    
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


def extract_gold_entities_from_ann(ann_file, use_component = False):
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

    for e in entities:
        if e['label'] == 'Target':
            e['std_text'] = canonical_target_name(e['text'])
        elif e['label'] in ['Element', 'Mineral']:
            e['std_text'] = canonical_component_name(e['text'])


    if use_component:
        for e in entities:
            if e['label'] in ['Element', 'Mineral']:
                e['label'] = 'Component'

    return entities


def get_entity_id(entity, tuple_level = False):
    # this function gets a mention-level entity id
    if tuple_level:
        if entity['label'] == "Target":
            name = canonical_target_name(entity['text'])
        elif entity['label'] in ['Element', 'Mineral', 'Component']:
            name = canonical_component_name(entity['text'])
        else:
            raise NameError(f"Currently do not support getting canonical texts for {entity['label']} entities. ")

        entity_id = f"{entity['venue']}, {entity['year']}, {entity['docname']}, {name}" 
    else: 
        entity_id = f"{entity['venue']}, {entity['year']}, {entity['docname']}, {entity['doc_start_char']}, {entity['doc_end_char']}"

    return entity_id




def extract_gold_relations_from_ann(ann_file, use_component = False):
    """ This function extract relations from ann files

    Args:
        ann_file: .ann file 
        use_component: whether to map element and mineral to component 
    """

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

    gold_entities = extract_gold_entities_from_ann(ann_file, use_component = use_component)
    annotid2entities = {e["annot_id"]: e for e in gold_entities}

    gold_relations = []
    for t, c, relation in annotid_annotid_relation:
        e1 = annotid2entities[t]
        e2 = annotid2entities[c]
        gold_relations.append((deepcopy(e1), deepcopy(e2), relation))

    return gold_relations

def extract_intrasent_goldrelations_from_ann(ann_file, corenlp_file = None, doc = None,use_component = False):
    """ This function extracts gold relations with entities in the same sentence

    Args:
        ann_file: .ann file 
    
        corenlp_file: file that stores corenlp's parsing in json file 
    
        doc: dictionary that stores corenlp's parsing
        
        use_component: whether to map element and mineral to component 
    """

    if doc is None and corenlp_file is None:
        raise NameError("Either doc_dict or corenlp_file must be provided ! ")
    if doc is None:
        # read corenlp file
        doc = json.load(open(corenlp_file, "r"))

    gold_relations = extract_gold_relations_from_ann(ann_file, use_component = use_component)

    offset2sentid = get_offset2sentid(doc = doc, corenlp_file = corenlp_file)

    intrasent_gold_relations = []
    for e1, e2, relation in gold_relations:
        sentid1 = get_sentid_from_offset(e1['doc_start_char'], e1['doc_end_char'], offset2sentid)
        sentid2 = get_sentid_from_offset(e2['doc_start_char'], e2['doc_end_char'], offset2sentid)

        if sentid1 is None or sentid2 is None: 
            continue 
        if sentid1 == sentid2:
            new_e1 = deepcopy(e1)
            new_e2 = deepcopy(e2)
            new_e1["sentid"] = sentid1
            new_e2["sentid"] = sentid2
            intrasent_gold_relations.append((new_e1, new_e2, relation))

    return intrasent_gold_relations

def get_offset2sentid(doc = None, corenlp_file = None):

    """ get a dictonary that maps character offset to sentid """

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
    """ This function gets the sent index given the character offset of an entity in the document 
    
    Args:
        doc_start_char: starting character offset of the entity in the document 
       
        doc_end_char: ending character offset of the entity in the document 
       
        offset2sentid: a mapping from character offset to sent index in the document 
    """
    sentid = None
    for offset in offset2sentid:
        if offset[0] <= doc_start_char < doc_end_char <= offset[1]:
            return offset2sentid[offset]
    return sentid 

def get_offset2docidx(doc = None, corenlp_file = None):
    """ 
    This function gets the mapping from the document-level offset of a word to its document-level word index 
    """

    # get a dictonary of character offset to sentid
    if doc is None and corenlp_file is None:
        raise NameError("Either doc_dict or corenlp_file must be provided ! ")
    if doc is None:
        # read corenlp file
        doc = json.load(open(corenlp_file, "r"))

    offset2idx = {}
    for sent in doc["sentences"]:
        for tok in sent['tokens']:
            offset = (tok["characterOffsetBegin"],  tok["characterOffsetEnd"])
            offset2idx[offset] = len(offset2idx)

    return offset2idx

def get_docidx_from_offset(doc_start_char, doc_end_char, offset2docidx):
    """
        This function gets the starting and ending document-level word indices for an entity given the entity's document-level offset. 
    """
    begin_idx = None
    end_idx = None # exclusive
    for offset in offset2docidx:
        if offset[0] <= doc_start_char < offset[1]:
            begin_idx = offset2docidx[offset]
        if  offset[0] < doc_end_char <= offset[1]:
            end_idx = offset2docidx[offset]
    return (begin_idx, end_idx)



def extract_intrasent_entitypairs_from_text_file(text_file, ann_file, doc = None, corenlp_file = None, use_component = False, use_sys_ners = False):
    
    """ 
    This function extract all pairs of entities from the same sentence as relation candidates. note that here we would get duplicated entity pairs with reverse order, such as (t1, t2) and (t2, t1)
    
    Args: 
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

    entities = extract_entities_from_text(text_file, ann_file, doc = doc, corenlp_file = corenlp_file, use_component = use_component, use_sys_ners = use_sys_ners)

    # get all possible entity pairs. 
    intrasent_entitypairs = []
    for i in range(len(entities)):
        for j in range(len(entities)):
            if i == j: continue
            if entities[i]['sentid'] != entities[j]['sentid']:
                continue
            # note that a entity may be annotated with different labels, and so entities[i] and entities[j] may correspond to the same annotated text (e.g., Dillinger at (2505, 2514)  of lpsc15-C-raymond-sol1159-v3-utf8/2620.ann is labeled Target and Unit at the same time)
            intrasent_entitypairs.append((deepcopy(entities[i]), deepcopy(entities[j])))
    return intrasent_entitypairs


def extract_entitypairs_from_text_file(text_file, ann_file, doc = None, corenlp_file = None, use_component = False, use_sys_ners = False, sent_window = 5):
    
    """ 

    This function extract all pairs of entities in a document as relation candidates. note that here we would get duplicated entity pairs with reverse order, such as (t1, t2) and (t2, t1)

    Args: 
        text_file: text_file that contains the journal/abstract 
        
        ann_file: file that contains annotations from brat. used to extract ners 

        doc:  a dictionary that stores corenlp's parsing for text_file

        corenlp_file: is a file that stores corenlp's parsing for text_file

        use_component: convert element and mineral to component if True

        use_sys_ners: extract system entities in corenlp_file constructed from the predictions NER model if True. Otherwise use gold entities

        sent_window: maximum number of sentences a pair of entities could be separated by. For example, if 0, then a pair of entities must lie in the same sentence. If 1, then a pair of entities could lie in both the same sentence and adjacent sentences. sent_window >= abs(sent index of entity1 - sent index of entity2). If sent_window is negative, all possible pairs of entities are extracted from a document. 
    """

    if doc is None and corenlp_file is None:
        raise NameError("Either doc_dict or corenlp_file must be provided ! ")
    if doc is None:
        # read corenlp file
        doc = json.load(open(corenlp_file, "r"))

    entities = extract_entities_from_text(text_file, ann_file, doc = doc, corenlp_file = corenlp_file, use_component = use_component, use_sys_ners = use_sys_ners)

    # get all possible entity pairs. 
    entitypairs = []
    for i in range(len(entities)):
        for j in range(len(entities)):
            if i == j: continue
            if sent_window < 0 or abs(entities[i]['sentid'] - entities[j]['sentid']) <= sent_window:
                # note that a entity may be annotated with different labels, and so entities[i] and entities[j] may correspond to the same annotated text (e.g., Dillinger at (2505, 2514)  of lpsc15-C-raymond-sol1159-v3-utf8/2620.ann is labeled Target and Unit at the same time)
                entitypairs.append((deepcopy(entities[i]), deepcopy(entities[j])))
    return entitypairs


def get_relation_coverage(entitypairs, gold_relations, tuple_level = False, all_entityid2ner = None):
    """
    This function calculates the coverage of gold relations in the extracted entity pairs
    
    Args:
        entitypairs: a list of pairs of entities extracted from text file 
        
        gold_relations: a list of pairs of entities and relation annotated
        
        tuple_level: a boolean indicating if the tuple_level statistics should be calculated. If True, tuple-level stats would be calculated (which means an entity is distinguished by its document offset and document id). Otherwise, instance-level (which means an entity is distinguished by its text and document id) stats would be calcualted. 
    """

    gold_ids = set()
    for entity1, entity2, relation in gold_relations:
        entity1_id = get_entity_id(entity1, tuple_level = tuple_level)
        entity2_id = get_entity_id(entity2, tuple_level = tuple_level)
        gold_ids.add(f"{entity1_id},,{entity2_id}")

    ids = set()
    for entity1, entity2 in entitypairs:
        entity1_id = get_entity_id(entity1, tuple_level = tuple_level
            )
        entity2_id = get_entity_id(entity2, tuple_level = tuple_level)

        ids.add(f"{entity1_id},,{entity2_id}")

    if all_entityid2ner is not None:
        extracted_entity1 = set()
        extracted_entity2 = set()

        for entity_id, ner in all_entityid2ner.items():
            if ner == 'Target':
                extracted_entity1.add(entity_id)
            if ner in ['Element', 'Mineral', 'Component']:
                extracted_entity2.add(entity_id)


    found_num = len(ids.intersection(gold_ids))
    found_percent = found_num/len(gold_ids)



    print(f">>> {'Tuple' if tuple_level else 'Instance'} Level Coverage:\n")

    print(f"{found_num}/{len(gold_ids)}({found_percent*100:.2f}%) of gold relations could be matched in entity pairs from texts")


    with open('missing_rels.txt', "w") as f:

        for entity1, entity2, relation in gold_relations:
            entity1_id = get_entity_id(entity1, tuple_level = tuple_level)
            entity2_id = get_entity_id(entity2, tuple_level = tuple_level)

            if f"{entity1_id},,{entity2_id}" not in ids:
                f.write(f"Missing relation ---\nENTITY1: {entity1}\n\nENTITY2:{entity2}\n\nEntity1 extracted: {entity1_id in extracted_entity1}, Entity2 extracted: {entity2_id in extracted_entity2}\n\n")

    print(f"missing relations are written to ./missing_rels.txt")

def get_entity_coverage(entities, gold_entities):
    """

    This function calculates the coverage of the gold entities in the extracted entities 
    
    Args:
        entities: a list of entities extracted from the text file 
        gold_entities: a list of gold entities 

    """
    gold_ids = set([f"{e['doc_start_char']} {e['doc_end_char']} {e['venue']} {e['year']} {e['docname']}" for e in gold_entities])
    ids = set([f"{e['doc_start_char']} {e['doc_end_char']} {e['venue']} {e['year']} {e['docname']}" for e in entities])

    found_gold = len(ids.intersection(gold_ids))
    found_percent = found_gold/len(gold_ids)
    nonexisting_num = len(ids - gold_ids)
    nonexisting_percent = nonexisting_num / len(ids)

    print(f"{found_gold}/{len(gold_ids)}({found_percent*100:.2f}%) of gold entities are extracted from texts")
    print(f"There are {nonexisting_num}/{len(ids)}({nonexisting_percent*100:.2f}%) nonexisting entities extracted")



if __name__ == "__main__":

    # sample codes to extract and check stats 
    use_sys_ners = 1
    use_component = 1
    print("Warning: the statistics are reported over ann files which have at least 1 Target and 1 Component. Ann files that are not satisfying this constraint would not be taken into consideration. ")
    if use_sys_ners:
        corenlp_dir = "../../parse-with-sysners"
    else:
        corenlp_dir = "../../parse/"


    gold_ids = set()
    ids = set()


    text_files = []
    inputdirs = [
    "../../corpus-LPSC/lpsc15-C-raymond-sol1159-v3-utf8", 
    "../../corpus-LPSC/lpsc16-C-raymond-sol1159-utf8/", 
    "../../corpus-LPSC/mpf-reviewed+properties-v2/", 
    "../../corpus-LPSC/phx-reviewed+properties-v2/"
    ]

    for inputdir in inputdirs:
        text_files.extend(glob.glob(join(inputdir, "*.txt")))

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

        entities.extend(extract_entities_from_text(text_file, ann_file,corenlp_file = corenlp_file,use_sys_ners = use_sys_ners, use_component = use_component))
        gold_entities.extend(extract_gold_entities_from_ann(ann_file, use_component = use_component))

        gold_relations.extend(extract_gold_relations_from_ann(ann_file, use_component = use_component))
        intrasent_goldrelations.extend(extract_intrasent_goldrelations_from_ann(ann_file, corenlp_file = corenlp_file, use_component = use_component))

        intrasent_entitypairs.extend(extract_intrasent_entitypairs_from_text_file(text_file, ann_file, corenlp_file = corenlp_file, use_sys_ners = use_sys_ners, use_component = use_component))


    task_entities = [e for e in entities if e['label'] in ['Target', 'Element', 'Mineral', 'Component']]
    task_gold_entities = [ e for e in gold_entities if e['label'] in ['Target', 'Element', 'Mineral', 'Component'] ]
    # get task-specific entities coverage 
    get_entity_coverage(task_entities, task_gold_entities)

    task_goldrelations = [(entity1, entity2, relation) for entity1, entity2, relation in gold_relations if entity1['label'] == 'Target' and entity2['label'] in ['Element', 'Mineral', 'Component'] and relation == 'Contains']

    task_intrasent_goldrelations = [(entity1,entity2, relation ) for entity1, entity2, relation in intrasent_goldrelations if entity1['label'] == 'Target' and entity2['label'] in ['Element', 'Mineral', 'Component'] and relation == 'Contains']

    task_intrasent_entitypairs = [(entity1, entity2) for entity1, entity2 in intrasent_entitypairs if entity1['label'] == 'Target' and entity2['label'] in ['Element', 'Mineral', 'Component']]

    # check relation extraction
    print()
    print(f"Task-specific Gold Relations: {len(task_goldrelations)} 'Contains' relations between Target and Component")
    print("Task-specific Intra-sentence Relation Coverage:")

    all_entityid2ner = {get_entity_id(e, tuple_level = False): e['label'] for e in entities}
    get_relation_coverage(task_intrasent_entitypairs, task_intrasent_goldrelations, tuple_level = False, all_entityid2ner = all_entityid2ner) 

# Copyright 2021, by the California Institute of Technology. ALL
# RIGHTS RESERVED. United States Government Sponsorship
# acknowledged. Any commercial use must be negotiated with the Office
# of Technology Transfer at the California Institute of Technology.
#
# This software may be subject to U.S. export control laws and
# regulations.  By accepting this document, the user agrees to comply
# with all applicable U.S. export laws and regulations.  User has the
# responsibility to obtain export licenses, or other export authority
# as may be required before exporting such information to foreign
# countries or providing access to foreign persons.
