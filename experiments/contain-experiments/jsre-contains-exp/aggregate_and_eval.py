import argparse, sys, os, json, io
from os.path import join, dirname, abspath, exists
# curpath = dirname(abspath(__file__))
curpath = abspath(".")
parentpath = dirname(curpath)
sys.path.append(parentpath)

from my_name_utils import canonical_elemin_name, canonical_target_name
from tuple_based_eval import get_eval_score

def aggregate_prediction(char_start_end1, char_start_end2, wordlevel_target_contain_elemin_mapping):
    # given two entities' start and end positions in the document, and a mapping of word-word-level prediciton, make the entity-entity-level prediction. the entity-entity is assigned with a contain relation if at least one word-word pair comes with a contain relation 
    for target in wordlevel_target_contain_elemin_mapping:
        start1, end1 = target
        if char_start_end1[0] <= start1 < end1 <= char_start_end1[-1]: # this means the word with start1 and end1 belongs to entity1
            for elemin in wordlevel_target_contain_elemin_mapping[(start1, end1)]:
                start2, end2 = elemin
                if char_start_end2[0] <= start2 < end2 <= char_start_end2[-1]: # this means that elemin is contained by target, and thus by entity1 
                    return 1
    return 0


def aggregate_document(sentid2info):
    entity_entity_relation = []
    for sentid in sentid2info:
        tokidx2info = {}
        queue = [] # store entities
        wordlevel_target_contain_elemin_mapping = {}
        for char_start_end1, char_start_end2, tok_idx1, tok_idx2, org_text1, org_text2, entity_ner_label1, entity_ner_label2, org_before_text1, org_before_text2, relation_label in sentid2info[sentid]:
            assert relation_label == 0 or relation_label == 1
            
            if relation_label == 1:
                if entity_ner_label1 == "Target" and (entity_ner_label2 == "Element" or entity_ner_label2 == "Mineral"):
                    if char_start_end1 not in wordlevel_target_contain_elemin_mapping:
                        wordlevel_target_contain_elemin_mapping[char_start_end1] = []
                    wordlevel_target_contain_elemin_mapping[char_start_end1].append(char_start_end2) 

            if tok_idx1 not in tokidx2info:
                tokidx2info[tok_idx1] = (char_start_end1, org_text1, entity_ner_label1, org_before_text1)

            if tok_idx2 not in tokidx2info:
                tokidx2info[tok_idx2] = (char_start_end2, org_text2, entity_ner_label2, org_before_text2)
        
        # merge to entity now 
        for tok_idx in sorted(tokidx2info.keys()):
            char_start_end, org_text, entity_ner_label, org_before_text = tokidx2info[tok_idx]
            tok_idx_range = (tok_idx, tok_idx + 1)
            if not len(queue): # empty queue
                queue.append((tok_idx_range, char_start_end, org_text, entity_ner_label))
            else:
                # if not empty, check if this tok could be merged into the last tok in the queue.
                # two toks could be merged if all of the follow could be satisfied:
                #   1. entity_ner_label is the same and they are not "O"
                #   2. last_tok_idx == tok_idx - 1, or last_tok_idx == tok_idx - 2 and last_org_text is a hypen or underscore
                last_tok_idx_range, last_char_start_end, last_org_text, last_entity_ner_label = queue[-1]

                should_merge = (last_entity_ner_label == entity_ner_label and entity_ner_label != "O") and (last_tok_idx_range[-1] == tok_idx_range[0] or (last_tok_idx_range[-1] == tok_idx_range[0] - 1 and (org_before_text == "-" or org_before_text == "_")))

                
                if should_merge:
                    last_org_text = "%s %s" % (last_org_text, org_text) if last_tok_idx_range[-1] == tok_idx_range[0] else "%s%s%s" % (last_org_text, org_before_text, org_text)
                    last_tok_idx_range = (last_tok_idx_range[0], tok_idx_range[-1])
                    last_char_start_end = (last_char_start_end[0], char_start_end[-1])

                    queue[-1] = (last_tok_idx_range, last_char_start_end, last_org_text, last_entity_ner_label)
                else:
                    queue.append((tok_idx_range, char_start_end, org_text, entity_ner_label))

        # merge relation prediction now 
        for i in range(len(queue)):
            _, char_start_end1, entity_text1, entity_ner_label1 = queue[i]
            if entity_ner_label1 != "Target":
                continue
            for j in range(len(queue)):
                if i == j: continue
                _, char_start_end2, entity_text2, entity_ner_label2 = queue[j]
                if entity_ner_label2 != "Element" and entity_ner_label2 != "Mineral":
                    continue
                
                has_relation = aggregate_prediction(char_start_end1, char_start_end2, wordlevel_target_contain_elemin_mapping)
                entity_entity_relation.append((entity_text1, entity_text2, has_relation))   

    # finally go through entity_entity_relation, standardize texts, and aggregate document-level prediction
    stdtexts2prediction = {}
    for entity_text1, entity_text2, has_relation in entity_entity_relation:
        std_entity_text1 = canonical_target_name(entity_text1)
        std_entity_text2 = canonical_elemin_name(entity_text2)


        stdtexts2prediction[(std_entity_text1, std_entity_text2)] = stdtexts2prediction.get((std_entity_text1, std_entity_text2), 0) or has_relation

    entity_entity_relation = [(std_entity_text1, std_entity_text2, has_relation) for (std_entity_text1, std_entity_text2), has_relation in stdtexts2prediction.items()]

    return entity_entity_relation









def aggregate(example_file, prediction_file):

    with io.open(example_file, "r", encoding = "utf8") as f:
        lines = [k for k in f.read().strip().split("\n") if k.strip() != ""]

    with io.open(prediction_file, "r", encoding = "utf8") as f:
        predicted_labels = [int(float(k)) for k in f.read().strip().split("\n") if k.strip() != ""]
    assert len(predicted_labels) == len(lines)
    # make doc2examples 
    doc2examples = {}
    for line, relation_label in zip(lines, predicted_labels):
        example_id = line.split("\t")[1]
        relation_label = int(relation_label)
        venue, year,fnbase,char_start_end1, char_start_end2, tok_idx1, tok_idx2, sentid, org_text1, org_text2, entity_ner_label1, entity_ner_label2, org_before_text1, org_before_text2 =  json.loads(example_id)
        docname = (venue, year, fnbase)
        if docname not in doc2examples:
            doc2examples[docname] = {}
        if sentid not in doc2examples[docname]:
            doc2examples[docname][sentid] = []
        doc2examples[docname][sentid].append((tuple(char_start_end1), tuple(char_start_end2), tok_idx1, tok_idx2, org_text1, org_text2, entity_ner_label1, entity_ner_label2, org_before_text1, org_before_text2, relation_label))
    
    # aggregate through each doc
    aggregate_predictions = []
    for (venue, year, fnbase) in doc2examples:
        for std_entity_text1, std_entity_text2, has_relation in aggregate_document(doc2examples[(venue, year, fnbase)]):
            aggregate_predictions.append((venue, year, fnbase
                    , std_entity_text1, std_entity_text2, has_relation))
    # print("saving to %s" % (outfile))
    # with io.open(outfile, 'w', 
    #              encoding='utf8') as f:
    #     for year, fnbase, std_entity_text1, std_entity_text2, has_relation in sorted(relation_preds, key = lambda x: x[1]):
    #         f.write("%s\t%s\t%s\t%s\t%d\n" % (year, fnbase, std_entity_text1, std_entity_text2, has_relation))

    return aggregate_predictions

def load_evalfile(eval_file):
    evals = []
    with io.open(eval_file, 'r', encoding = "utf8") as f:
        lines = [ k for k in f.read().strip().split("\n") if k.strip() != ""]
        for line in lines:
            venue, year, fnbase, std_entity_text1, std_entity_text2 = line.split("\t")
            evals.append((venue, year, fnbase, std_entity_text1, std_entity_text2))
    return evals

def check_gold_coverage_by_examples(aggregate_predictions, evals, temp_analysis_dir = "./temp"):
    if not exists(temp_analysis_dir):
        os.makedirs(temp_analysis_dir)

    example_set = set([(venue, year, fnbase, std_entity_text1, std_entity_text2) for venue,  year, fnbase, std_entity_text1, std_entity_text2, has_relation in aggregate_predictions])
    with open(join(temp_analysis_dir, "tuples.txt"), "w") as f:
        f.write("\n".join(sorted(set(["%s, %s, %s, %s, %s" %(venue, year, fnbase, std_entity_text1, std_entity_text2) for venue, year, fnbase, std_entity_text1, std_entity_text2 in example_set]))))

    found_gold = 0
    print(">>>> Samples in Evaluation set that couldn't be found in input merged entities")
    missing_tuples = set()
    for k in evals:
        if k in example_set:
            found_gold += 1
        else:
            missing_tuples.add("%s, %s, %s, %s, %s" % k )
    with open(join(temp_analysis_dir, "missing_tuples.txt"), 'w') as f:
        f.write("\n".join(sorted(missing_tuples)))
        
    print("%s/%s(%s) samples in evaluation set is found in predicted examples (regardless of the prediction label)" % (str(found_gold), str(len(evals)), str(found_gold * 1.0 / len(evals))))
    print()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--examples", help = "mode.predict",required = True)
    parser.add_argument("--predictions", help = "mode.output",required = True)
    parser.add_argument("--evals", help = "mode-Contains.std_eval",required = True)



    parser.add_argument("--outfile", required = True)
    args = parser.parse_args()

    aggregate_predictions = aggregate(args.examples, args.predictions)
    evals = load_evalfile(args.evals)
    check_gold_coverage_by_examples(aggregate_predictions, evals)
    
    aggregate_contain_relations = [ (venue, year, fnbase, std_entity_text1, std_entity_text2) for venue, year, fnbase
                    , std_entity_text1, std_entity_text2, has_relation in aggregate_predictions if has_relation]

    precision, recall, f1 = get_eval_score(
        [("%s-%s-%s"%(venue, year, fnbase), std_entity_text1, std_entity_text2) for venue, year, fnbase, std_entity_text1, std_entity_text2 in aggregate_contain_relations], 
        [("%s-%s-%s"%(venue, year, fnbase), std_entity_text1, std_entity_text2) for venue, year, fnbase, std_entity_text1, std_entity_text2 in evals])

    print(">>>> precision: %s, recall: %s, f1: %s" % (str(precision), str(recall), str(f1)))

