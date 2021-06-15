import re, pickle, sys, argparse, random, json, os, pickle
from sys import stdout
from copy import deepcopy 
from os.path import abspath, dirname, join, exists
from os import makedirs, listdir

# curpath = dirname(abspath(__file__))
curpath = abspath(".")
upperpath = dirname(curpath)
sys.path.append(upperpath)

from instance import Span_Instance, Rel_Instance 
parentpath = dirname(upperpath)
sys.path.insert(0, parentpath)
from extraction_utils import get_docid, extract_gold_entities_from_ann,extract_intrasent_entitypairs_from_text_file, extract_intrasent_goldrelations_from_ann, extract_entities_from_text, get_offset2sentid, get_sentid_from_offset, extract_gold_relations_from_ann

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

def inconsistent_nested_entities_prediction(pred_instances):
	tarID2compOffset2prediction = {}
	for rel in sorted(pred_instances, key = lambda x: x.span2.doc_end_char - x.span2.doc_start_char, reverse = True):
		target = rel.span1
		component = rel.span2
		relation = rel.pred_relation_label 

		tarID = target.span_id
		curbegin, curend = component.doc_start_char, component.doc_end_char

		if tarID not in tarID2compOffset2prediction:
			tarID2compOffset2prediction[tarID] = {(curbegin, curend): [relation]}
		else:
			inside = 0
			for (begin, end) in tarID2compOffset2prediction[tarID]:
				if  begin <= curbegin < curend <= end:
					inside = 1
					tarID2compOffset2prediction[tarID][(begin, end)].append(relation)
			if not inside:
				tarID2compOffset2prediction[tarID][(curbegin, curend)] = [relation]
	count_nested_predictions = 0
	count_different_nested_predictions = 0 
	count_single_nested_predictions = 0 
	count_predictions = 0 
	for tarID in tarID2compOffset2prediction:
		for compOffset in tarID2compOffset2prediction[tarID]:
			
			predictions = tarID2compOffset2prediction[tarID][compOffset]

			count_predictions += len(predictions)

			if len(predictions) > 1:
				count_nested_predictions += len(predictions)
				count_single_nested_predictions += 1

				count_different_nested_predictions += 1 if len(set(predictions)) > 1 else 0 
	print(">>>Nested Entities Predictions:")
	print(f"   In total there {count_predictions} predictions, with {count_nested_predictions}({count_nested_predictions/count_predictions*100:.2f}%) of them are nested predictions. These nested predictions have could be reduced to {count_single_nested_predictions} single predictions. {count_different_nested_predictions} ({count_different_nested_predictions/count_single_nested_predictions*100:.2f}%) of these single predictions have inconsistent nested predictions.   ")

def nested_entities_annotation(ann_files, relation_type):
	tarID2compOffset2annotation = {}
	for ann_file in ann_files:
		gold_relations = [(e1, e2, relation) for e1, e2, relation in extract_gold_relations_from_ann(ann_file) if e1['label'] == 'Target' and e2['label'] in ['Element', 'Mineral']]

		for tar, comp, relation in sorted(gold_relations, key = lambda x: x[1]['doc_end_char'] - x[1]['doc_start_char'], reverse = True):
			tarID = f"{tar['year']},{tar['venue']}, {tar['docname']},{tar['doc_start_char']},{tar['doc_end_char']}"
			if tarID not in tarID2compOffset2annotation:
				tarID2compOffset2annotation[tarID] = {}
			curbegin, curend = comp['doc_start_char'], comp['doc_end_char']
			
			is_inside = 0 
			for begin, end in tarID2compOffset2annotation[tarID]:
				if begin <= curbegin < curend <= end:
					is_inside = 1
					tarID2compOffset2annotation[tarID][(begin, end)].append((comp['text'], relation))
			if not is_inside:
				tarID2compOffset2annotation[tarID][(curbegin, curend)] = [(comp['text'], relation)]
	nested_inrelation_entities_single_count = 0 
	nested_inrelation_entities = 0
	for tarID in tarID2compOffset2annotation:
		for begin, end in tarID2compOffset2annotation[tarID]:
			annotations = tarID2compOffset2annotation[tarID][(begin, end)]
			if len(annotations) > 1:
				print(tarID, annotations)
				nested_inrelation_entities += len(annotations)
				nested_inrelation_entities_single_count += 1

	print(f"There are {nested_inrelation_entities_single_count} single entities annotated with several relations to its smaller entities. ")
	print()

	count = 0 
	for tarID in tarID2compOffset2annotation:
		for begin, end in tarID2compOffset2annotation[tarID]:
			annotations = tarID2compOffset2annotation[tarID][(begin, end)]
			if len(annotations) == 1 and len(annotations[0][0].split()) > 1:
				print(tarID, annotations)
				count += 1
	print(count)


def containee_score(pred_rel_instances, gold_rel_instances):
	pred_instances = pred_rel_instances
	gold_instances = gold_rel_instances
	# eval over contained components
	containees = set()

	for rel in pred_instances:
		if rel.pred_relation_label == 'Contains':
			containees.add((rel.span2.venue, rel.span2.year, rel.span2.docname,rel.span2.span_id, rel.span2.std_text))
	gold_containees = set()
	gold_containee_texts = set()
	for rel in gold_instances:
		if rel.label == 'Contains':
			gold_containees.add((rel.span2.venue, rel.span2.year, rel.span2.docname, rel.span2.span_id, rel.span2.std_text))
			gold_containee_texts.add((rel.span2.venue, rel.span2.year, rel.span2.docname, rel.span2.std_text))
	print(f"There are {len(gold_containees)} gold instances at instance level, and {len(gold_containee_texts)} at text level ")


	# tuple level eval 
	predictions = set([(venue, year, docname, std_text) for venue, year, docname, span_id, std_text in containees])
	golds = set([(venue, year, docname, std_text) for venue, year, docname, span_id, std_text in gold_containees])
	correct = len(predictions.intersection(golds))
	precision = correct / len(predictions) if len(predictions) != 0 else 0  
	recall = correct / len(golds) if len(golds) != 0 else 0 
	f1 = precision * recall * 2 / (precision + recall) if precision + recall != 0 else 0 

	print(f"Tuple Level Containee: P = {precision*100:.2f}, R = {recall * 100:.2f}, F1 = {f1*100:.2f}")

	# instance level 
	predictions = set([span_id for venue, year, docname, span_id, std_text in containees])
	golds = set([span_id for venue, year, docname, span_id, std_text in gold_containees])
	correct = len(predictions.intersection(golds))
	precision = correct / len(predictions) if len(predictions) != 0 else 0  
	recall = correct / len(golds) if len(golds) != 0 else 0 
	f1 = precision * recall * 2 / (precision + recall) if precision + recall != 0 else 0 
	print(f"Instance Level Containee: P = {precision*100:.2f}, R = {recall * 100:.2f}, F1 = {f1*100:.2f}")

	print("all yes baseline ")
	containees = set()
	for rel in pred_instances:
		containees.add((rel.span2.venue, rel.span2.year, rel.span2.docname,rel.span2.span_id, rel.span2.std_text))
	# tuple level eval 
	predictions = set([(venue, year, docname, std_text) for venue, year, docname, span_id, std_text in containees])
	golds = set([(venue, year, docname, std_text) for venue, year, docname, span_id, std_text in gold_containees])
	correct = len(predictions.intersection(golds))
	precision = correct / len(predictions) if len(predictions) != 0 else 0  
	recall = correct / len(golds) if len(golds) != 0 else 0 
	f1 = precision * recall * 2 / (precision + recall) if precision + recall != 0 else 0 
	print(f"Tuple Level Containee: P = {precision*100:.2f}, R = {recall * 100:.2f}, F1 = {f1*100:.2f}")
	
	# instance level 
	predictions = set([span_id for venue, year, docname, span_id, std_text in containees])
	golds = set([span_id for venue, year, docname, span_id, std_text in gold_containees])
	correct = len(predictions.intersection(golds))
	precision = correct / len(predictions) if len(predictions) != 0 else 0  
	recall = correct / len(golds) if len(golds) != 0 else 0 
	f1 = precision * recall * 2 / (precision + recall) if precision + recall != 0 else 0 
	print(f"Instance Level Containee: P = {precision*100:.2f}, R = {recall * 100:.2f}, F1 = {f1*100:.2f}")


def container_score(pred_rel_instances, gold_rel_instances):
	pred_instances = pred_rel_instances
	gold_instances = gold_rel_instances
	# eval over contained components
	containers = set()

	for rel in pred_instances:
		if rel.pred_relation_label == 'Contains':
			containers.add((rel.span1.venue, rel.span1.year, rel.span1.docname,rel.span1.span_id, rel.span1.std_text))
	gold_containers = set()
	gold_container_texts = set()
	for rel in gold_instances:
		if rel.label == 'Contains':
			gold_containers.add((rel.span1.venue, rel.span1.year, rel.span1.docname, rel.span1.span_id, rel.span1.std_text))
			gold_container_texts.add((rel.span1.venue, rel.span1.year, rel.span1.docname, rel.span1.std_text))
	print(f"There are {len(gold_containers)} gold instances at instance level, and {len(gold_container_texts)} at text level ")


	# tuple level eval 
	predictions = set([(venue, year, docname, std_text) for venue, year, docname, span_id, std_text in containers])
	golds = set([(venue, year, docname, std_text) for venue, year, docname, span_id, std_text in gold_containers])
	correct = len(predictions.intersection(golds))
	precision = correct / len(predictions) if len(predictions) != 0 else 0  
	recall = correct / len(golds) if len(golds) != 0 else 0 
	f1 = precision * recall * 2 / (precision + recall) if precision + recall != 0 else 0 

	print(f"Tuple Level Container: P = {precision*100:.2f}, R = {recall * 100:.2f}, F1 = {f1*100:.2f}")

	# instance level 
	predictions = set([span_id for venue, year, docname, span_id, std_text in containers])
	golds = set([span_id for venue, year, docname, span_id, std_text in gold_containers])
	correct = len(predictions.intersection(golds))
	precision = correct / len(predictions) if len(predictions) != 0 else 0  
	recall = correct / len(golds) if len(golds) != 0 else 0 
	f1 = precision * recall * 2 / (precision + recall) if precision + recall != 0 else 0 
	print(f"Instance Level Container: P = {precision*100:.2f}, R = {recall * 100:.2f}, F1 = {f1*100:.2f}")

	print("all yes baseline ")
	containers = set()
	for rel in pred_instances:
		containers.add((rel.span1.venue, rel.span1.year, rel.span1.docname,rel.span1.span_id, rel.span1.std_text))
	# tuple level eval 
	predictions = set([(venue, year, docname, std_text) for venue, year, docname, span_id, std_text in containers])
	golds = set([(venue, year, docname, std_text) for venue, year, docname, span_id, std_text in gold_containers])
	correct = len(predictions.intersection(golds))
	precision = correct / len(predictions) if len(predictions) != 0 else 0  
	recall = correct / len(golds) if len(golds) != 0 else 0 
	f1 = precision * recall * 2 / (precision + recall) if precision + recall != 0 else 0 
	print(f"Tuple Level Container: P = {precision*100:.2f}, R = {recall * 100:.2f}, F1 = {f1*100:.2f}")
	
	# instance level 
	predictions = set([span_id for venue, year, docname, span_id, std_text in containers])
	golds = set([span_id for venue, year, docname, span_id, std_text in gold_containers])
	correct = len(predictions.intersection(golds))
	precision = correct / len(predictions) if len(predictions) != 0 else 0  
	recall = correct / len(golds) if len(golds) != 0 else 0 
	f1 = precision * recall * 2 / (precision + recall) if precision + recall != 0 else 0 
	print(f"Instance Level Container: P = {precision*100:.2f}, R = {recall * 100:.2f}, F1 = {f1*100:.2f}")



def train_dev_test_distribution(train_annfiles, train_textfiles, train_corenlpfiles, dev_annfiles, dev_textfiles, dev_corenlpfiles, test_annfiles, test_textfiles, test_corenlpfiles):
	for name, ann_files, text_files, corenlp_files in zip(["TRAIN", 'DEV','TEST'], [train_annfiles, dev_annfiles, test_annfiles], [train_textfiles, dev_textfiles, test_textfiles], [train_corenlpfiles, dev_corenlpfiles, test_corenlpfiles]):
		count_pos = 0 
		count_neg = 0 
		for ann_file, text_file, corenlp_file in zip(ann_files, text_files, corenlp_files):
			entitypairs = [(e1, e2) for e1, e2 in extract_intrasent_entitypairs_from_text_file(text_file, ann_file, corenlp_file = corenlp_file, use_component = True) if e1['label'] == 'Target' and e2['label'] == 'Component']

			gold_relations = extract_intrasent_goldrelations_from_ann(ann_file, corenlp_file = corenlp_file, use_component = True)

			gold_ids = set([ f"{e1['doc_start_char']},{e1['doc_end_char']},{e2['doc_start_char']},{e2['doc_end_char']}" for e1, e2, relation in gold_relations if e1['label'] == 'Target' and e2['label'] == 'Component' and relation == 'Contains'])
			entitypair_ids = set([f"{e1['doc_start_char']},{e1['doc_end_char']},{e2['doc_start_char']},{e2['doc_end_char']}" for e1, e2 in entitypairs])
			count_pos += len(gold_ids)
			count_neg += len(entitypair_ids - gold_ids)

		print(f"In {name} set, there are {count_pos}({count_pos/(count_pos + count_neg) * 100:.2f}) POS REL instances and {count_neg} NEG REL instances for predictions")
		print()







def main():
	# train_annfiles, train_textfiles, train_corenlpfiles, dev_annfiles, dev_textfiles, dev_corenlpfiles, test_annfiles, test_textfiles, test_corenlpfiles = load_files()
	# pred_instances = pickle.load(open("./temp/rel/predictions.pkl", "rb"))
	# inconsistent_nested_entities_prediction(pred_instances)

	# nested_entities_annotation(train_annfiles + dev_annfiles + test_annfiles, 'Contains')

	pred_instances = pickle.load(open("./temp/rel/predictions.pkl", "rb"))
	gold_instances = pickle.load(open("./data/dev/gold_relins.pkl", "rb"))
	containee_score(pred_instances, gold_instances)
	container_score(pred_instances, gold_instances)


	# train_dev_test_distribution(train_annfiles, train_textfiles, train_corenlpfiles, dev_annfiles, dev_textfiles, dev_corenlpfiles, test_annfiles, test_textfiles, test_corenlpfiles)


if __name__ == "__main__":
	main()
