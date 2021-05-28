# This function makes within sentence instances and removes duplicates based on texts
import re, pickle, sys, argparse, random, json, os
from sys import stdout 
from os.path import abspath, dirname, join, exists
from os import makedirs, listdir
from transformers import *

curpath = dirname(abspath(__file__))
upperpath = dirname(curpath)
sys.path.append(upperpath)
from instance import Span_Instance, Rel_Instance
from config import label2ind, ind2label, tokenizer_type


parentpath = dirname(upperpath)
sys.path.insert(0, parentpath)
from convertedReader import read_converted, get_docid

tokenizer = BertTokenizerFast.from_pretrained(tokenizer_type)


def make_relation_samples(mode, convfiles,annfiles, outdir, accept_subject2object, use_gold_entities = True, max_len = 512, temp_analysis_dir = "./temp"):

    if not exists(temp_analysis_dir):
        os.makedirs(temp_analysis_dir)
    # first collect all valid entity pairs for predictions. this is instance-based, which only relies on character offset 
    extracted_relins = []
    failed_examples = 0 
    collected_relations = []
    for convfile, annfile in zip(convfiles, annfiles):
        venue, year, docname, _ = get_docid(convfile)
        rel_ins,cur_failed_examples = extract_relins_from_converted_file(convfile, accept_subject2object, use_gold_entities = use_gold_entities, max_len = max_len)
       
       

        # load relation id 2 relation label from annfile
        failed_examples += cur_failed_examples
        extracted_relins.extend(rel_ins)

        collected_relations += [f"{venue}, {year}, {docname}, {rel.span1.text}, {rel.span2.text}, {rel.span1.std_text, rel.span2.std_text}" for rel in rel_ins]

    with open(join(temp_analysis_dir, "instances.txt"), "w") as f:
        f.write("\n".join(sorted(set(collected_relations))))

    print(f"failed to insert type markers in {failed_examples} examples")
    # load annoatated gold relations. this is for evaluation 
    gold_relins = make_gold_relins(annfiles, convfiles, accept_subject2object) # both are in instance level, and gold_relations_instance_level is instance level 

    # make a mapping fom relation id to relation, in order to assign the gold relation label to all relation instances in extracted_relins 
    relid2goldlabel = {rel.re_id: rel.label for rel in gold_relins}

    # coverage at instance level, measured by re_id
    found = len(set([rel.re_id for rel in extracted_relins]).intersection(set(relid2goldlabel.keys())))
    print(f"{found}/{len(relid2goldlabel)}({found/len(relid2goldlabel)}) gold relations(instance-level) are found in the extracted instances")

    # coverage at tuple level, measured by signatures
    found_tuple_based = len(set([rel.signature for rel in extracted_relins]).intersection(set([rel.signature for rel in gold_relins])))

    print(f"{found_tuple_based}/{len(set([rel.signature for rel in gold_relins]))}({found_tuple_based/len(set([rel.signature for rel in gold_relins]))}) gold relations(tuple-level) are found in the extracted instances")


    # assign relation label to extracted rel instance according to annfile and relation_id
    for i, rel in enumerate(extracted_relins):
        extracted_relins[i].label = "Contains" if rel.re_id in relid2goldlabel else 'O'

    if not exists(outdir):
        os.makedirs(outdir)


    # now print out stats
    count_pos = len([1 for rel in extracted_relins if rel.label == "Contains"])
    count_neg = len(extracted_relins) - count_pos
    if use_gold_entities:
        print(f"Extracted gold relations instances (instance-based) for training/predictions: {count_pos} positive and {count_neg} negative ")
    else:
        print(f"Extracted system relations instances (instance-based, predicted by NER model) for training/predictions: {count_pos} positive and {count_neg} negative ")

    if not exists(outdir):
        os.makedirs(outdir)

    outfile = join(outdir, f"{mode}.extracted_{'gold' if use_gold_entities else 'system'}_relins.pkl")
    print(f"saving to {outfile}")
    with open(outfile, "wb") as f:
        pickle.dump(extracted_relins, f)

    outfile = join(outdir, f"{mode}.annotated_gold_relins.pkl")
    print(f"saving the evaluation set to {outfile}")
    with open(outfile, "wb") as f:
        pickle.dump(gold_relins, f)

    print()


def extract_relins_from_converted_file(convfile, accept_subject2object, use_gold_entities = True, max_len = 512):
    

    rel_ins = []

    venue, year, docname, _ = get_docid(convfile)

    doc = read_converted(convfile)

    entities = doc["predicted_entities"] if not use_gold_entities else doc["gold_entities"]

    # entities is a list of list, each list is a sentence. here we take only entity pairs from the same sentence
    failed_examples = 0
    for sentence_entities in entities:
        sentid = sentence_entities[0]["sentid"]
        sent_toks = doc["sents"][sentid]


        for i in range(len(sentence_entities)):
            entity1 = sentence_entities[i]
            ner1 = entity1["predicted_ner"] if not use_gold_entities else entity1["gold_ner"]

            
            span1 = Span_Instance(venue, year, docname, entity1["doc_start_char"], entity1["doc_end_char"],  entity1["text"].lower(), ner1, sent_toks = sent_toks,  sentid = entity1["sentid"], sent_start_idx =entity1["sent_start_idx"], sent_end_idx = entity1["sent_end_idx"])

           


            
            if ner1 not in accept_subject2object:
                continue

            for j in range(len(sentence_entities)):
                if j == i: continue
                entity2 = sentence_entities[j]

                ner2 = entity2["predicted_ner"] if not use_gold_entities else entity2["gold_ner"]

                
                if ner2 not in accept_subject2object[ner1]:
                    continue

                span2 = Span_Instance(venue, year, docname, entity2["doc_start_char"], entity2["doc_end_char"],  entity2["text"].lower(), ner2, sent_toks = sent_toks,  sentid = entity2["sentid"], sent_start_idx =entity2["sent_start_idx"], sent_end_idx = entity2["sent_end_idx"])
                
                rel = Rel_Instance(span1, span2)
                # insert type markers into input ids around two entities. The returned value identifies if the inserting is successful
                success = rel.insert_type_markers(tokenizer, max_len = max_len)

                if success:
                    rel_ins.append(rel)
                else:
                    failed_examples += 1




    return rel_ins, failed_examples

def get_gold_annotid(annfile):
    # only get allowed ner types 
    annotid2position_ner = {}
    annotid2text = {}
    with open(annfile, "r") as f:
        for k in f.readlines():
            k = k.strip()
            if len(k.split("\t")) == 3:
                annot_id, label, span = k.split("\t")
                assert annot_id not in annotid2position_ner

                label, doc_start_char, doc_end_char = label.split()
                doc_start_char = int(doc_start_char)
                doc_end_char = int(doc_end_char)
                if annot_id[0] == "T":
                    annotid2position_ner[annot_id] = (doc_start_char, doc_end_char, label)
                    annotid2text[annot_id] = span.lower()
    return annotid2position_ner, annotid2text

def make_gold_relins(annfiles, convfiles, accept_subject2object):
    # convfile is used to check if the relations cross sentences

    print("WARNING: only use and evaluate with the relations not crossing sentences")

    gold_relins = [] # this doesn't count cross sentence instance. Instance level 

    for filenum, (annfile, convfile) in enumerate(zip(annfiles, convfiles)):


        # currently this functions is tested only over lpsc, mpf and phx dataset 
        assert "mpf" in annfile.lower() or "phx" in annfile.lower() or "lpsc" in annfile.lower()
        is_mpfphx = "mpf" in annfile.lower() or "phx" in annfile.lower() # phx and mpf use different representation in ann file than lpsc documents. So we need different ways handling them.
        
        venue, year, docname, _ = get_docid(convfile)
        doc = read_converted(convfile)

        entity_entity_relation = []

        annotid2position_ner, annotid2text = get_gold_annotid(annfile)

        annotid_annotid_relation = []
        all_instances = set() # includes cross sentence and within sentence instances

        # this for loop extracts gold relations correctly and could match the statistics
        for annotation_line in open(annfile).readlines():
            if annotation_line.strip() == "": continue
            splitline = annotation_line.strip().split('\t')
            annot_id = splitline[0]

            if is_mpfphx:
                if splitline[0][0] == "R":
                    args = splitline[1].split()
                    if len(args) == 3:
                        relation = args[0]
                        arg1 = args[1].split(":")[1]
                        arg2 = args[2].split(":")[1]
                        entity_entity_relation.append((arg1, arg2, relation))

            else:
                if splitline[0][0] == 'E': # event
                    args         = splitline[1].split() 
                    relation   = args[0].split(':')[0]
                    
                    anchor  = args[0].split(':')[1]
                    args         = [a.split(':') for a in args[1:]]
                    targets = [v for (t,v) in args if t.startswith('Targ')]
                    cont    = [v for (t,v) in args if t.startswith('Cont')]

                    for t in targets:
                        for c in cont:
                            entity_entity_relation.append((t, c, relation))


        for t, c, relation in entity_entity_relation:
            type1 = annotid2position_ner[t][-1]
            type2 = annotid2position_ner[c][-1]
            if type1 in accept_subject2object and type2 in accept_subject2object[type1] and relation == "Contains": 
                doc_start1, doc_end1 = annotid2position_ner[t][:2]
                doc_start2, doc_end2 = annotid2position_ner[c][:2]
                ttext = annotid2text[t]
                ctext = annotid2text[c]
                
                sentid1 = -1 
                for bound in doc["char2sentid"]:
                    if bound[0] <= doc_start1 < bound[1]:
                        sentid1 = doc["char2sentid"][bound]
                        break
                assert sentid1 != -1

                sentid2 = -1 
                for bound in doc["char2sentid"]:
                    if bound[0] <= doc_start2 < bound[1]:
                        sentid2 = doc["char2sentid"][bound]
                        break
                assert sentid2 != -1

                if sentid1 != sentid2:
                    continue

                span1 = Span_Instance(venue, year, docname, doc_start1, doc_end1,  ttext, type1, sentid = sentid1)
                span2 = Span_Instance(venue, year, docname, doc_start2, doc_end2,  ctext, type2, sentid = sentid2)

                rel = Rel_Instance(span1, span2, label_str = relation)

                gold_relins.append(rel)

    print(f"collect {len(gold_relins)} instance-level gold relations ")
   
    return gold_relins



# python make_train_dev_test.py > ./stat/train_dev_test.txt
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-mode', choices = ["Merged", "EM", "E", "M"], help = "what experiments to run (e.g., elements, minerals, and their merged set)", required= True)
    parser.add_argument('-add_mpfphx', choices = [0, 1], type = int, default = 0 )

    parser.add_argument('-use_mpfphx_only', choices = [0, 1], type = int, default = 0 )
    

    args = parser.parse_args()

    # =============================
    mode = args.mode
    if mode == "Merged":
        accept_subject2object = {
            "Target":
                {"Element", "Mineral"}
        }
    else:
        d = {
        "E": "Element", 
        "M": "Mineral"}
        accept_subject2object = {"Target":set()}

        for c in mode:
            accept_subject2object["Target"].add(d[c])

    outdir = join(curpath, "rels")

    # make training/val/test instances, and gold spans
    converted15_indir = join(dirname(parentpath), "data/converted/corpus-LPSC-with-ner/lpsc15")
    ann15_indir = join(dirname(parentpath), "data/corpus-LPSC/lpsc15")

    # ---- make training samples ----
    print(" ----- making training samples ... ")

    train_outdir = join(outdir, "train")
    train_convfiles = [join(converted15_indir, file.split(".ann")[0] + ".txt") for file in listdir(ann15_indir) if file.endswith(".ann")][:42]
    train_annfiles = [join(ann15_indir, file) for file in listdir(ann15_indir) if file.endswith(".ann")][:42]
    # use gold entities in prediction time 
    gold_relations1 = make_relation_samples(mode, train_convfiles,train_annfiles, train_outdir,  accept_subject2object, use_gold_entities = True)

    # # use entities extracted by ner systems in prediction time 
    # make_relation_samples(train_convfiles,train_annfiles, train_outdir, use_gold_entities = False)


    # ---- make val samples ----
    print(" ----- making val samples ... ")

    val_outdir = join(outdir, "val")
    val_convfiles = [join(converted15_indir, file.split(".ann")[0] + ".txt") for file in listdir(ann15_indir) if file.endswith(".ann")][42:]
    val_annfiles = [join(ann15_indir, file) for file in listdir(ann15_indir) if file.endswith(".ann")][42:]

    gold_relations2 =  make_relation_samples(mode, val_convfiles, val_annfiles, val_outdir,  accept_subject2object, use_gold_entities = True)

    # make_relation_samples(val_convfiles, val_annfiles, val_outdir, use_gold_entities = False)



    # -------- make test samples ---------
    print(" ----- making test samples ... ")

    converted16_indir = join(dirname(parentpath), "data/converted/corpus-LPSC-with-ner/lpsc16")
    ann16_indir = join(dirname(parentpath), "data/corpus-LPSC/lpsc16")

    test_convfiles = [join(converted16_indir, file.split(".ann")[0] + ".txt") for file in listdir(ann16_indir) if file.endswith(".ann")]

    test_annfiles = [join(ann16_indir, file) for file in listdir(ann16_indir) if file.endswith(".ann")]

    def add_mpfphx(test_convfiles, test_annfiles):
        convertedmpf_indir = join(dirname(parentpath), "data/converted/corpus-LPSC-with-ner/mpf-reviewed+properties-v2")
        annmpf_indir = join(dirname(parentpath), "data/corpus-LPSC/mpf-reviewed+properties-v2")
        test_convfiles += [join(convertedmpf_indir, file) for file in listdir(convertedmpf_indir) if file.endswith(".txt")]
        test_annfiles += [join(annmpf_indir, file.split(".txt")[0] + ".ann") for file in listdir(convertedmpf_indir) if file.endswith(".txt")]

        convertedphx_indir = join(dirname(parentpath), "data/converted/corpus-LPSC-with-ner/phx-reviewed+properties")
        annphx_indir = join(dirname(parentpath), "data/corpus-LPSC/phx-reviewed+properties")
        test_convfiles += [join(convertedphx_indir, file) for file in listdir(convertedphx_indir) if file.endswith(".txt")]
        test_annfiles += [join(annphx_indir, file.split(".txt")[0] + ".ann") for file in listdir(convertedphx_indir) if file.endswith(".txt")]
        return test_convfiles, test_annfiles

    if args.add_mpfphx:
        test_convfiles, test_annfiles = add_mpfphx(test_convfiles, test_annfiles)

    if args.use_mpfphx_only:
        test_convfiles, test_annfiles = add_mpfphx([], [])



    test_outdir = join(outdir,"test")

    gold_relations3 = make_relation_samples(mode, test_convfiles, test_annfiles, test_outdir, accept_subject2object, use_gold_entities = True, max_len = 512)




