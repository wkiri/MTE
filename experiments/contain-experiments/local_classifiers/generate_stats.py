import re, pickle, sys, argparse, random, json, os
from sys import stdout
from copy import deepcopy 
from os.path import abspath, dirname, join, exists
from os import makedirs, listdir

# curpath = dirname(abspath(__file__))
curpath = abspath(".")
upperpath = dirname(curpath)
sys.path.append(upperpath)
from extraction_utils import get_docid, extract_gold_entities_from_ann,extract_intrasent_entitypairs_from_text_file, extract_intrasent_goldrelations_from_ann, extract_entities_from_text, get_offset2sentid, get_sentid_from_offset, extract_gold_relations_from_ann

def load_files():
    proj_path = dirname(dirname(dirname(curpath)))
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


def percentage_entities_in_relation(train_annfiles, train_corenlpfiles, dev_annfiles, dev_corenlpfiles, ners, relation_type, intrasent_relation = True, 
	entity_cooccur_with_target = True, test_annfiles = [], test_corenlpfiles = [], tuple_level = False):
	
	for ann_files, corenlp_files, name in zip([train_annfiles, dev_annfiles, test_annfiles], [train_corenlpfiles, dev_corenlpfiles, test_corenlpfiles], ['TRAIN', 'DEV', 'TEST']):
		if len(ann_files) == 0: continue
		
		inrelation_count = 0 
		entity_count = 0 
		for ann_file, corenlp_file in zip(ann_files, corenlp_files):
			
			doc = json.load(open(corenlp_file, "r"))
			
			gold_entities = [e for e in extract_gold_entities_from_ann(ann_file) ]
			if not entity_cooccur_with_target:
				gold_entities = [e for e in gold_entities if e['label'] in ners]
			else:
				# require the sentence of the entity to have at least one target
				offset2sentid = get_offset2sentid(doc = doc, corenlp_file = corenlp_file)
				sentid2entities = {}
				for e in gold_entities:
					if not (e['label'] in ners or e['label'] == 'Target'):
						continue
					sentid = get_sentid_from_offset(e['doc_start_char'], e['doc_end_char'], offset2sentid)
					if sentid not in sentid2entities:
						sentid2entities[sentid] = []
					sentid2entities[sentid].append(e)
				gold_entities = []
				for _, sentence_entities in sentid2entities.items():
					if 'Target' in set([e['label'] for e in sentence_entities]):
						gold_entities.extend([e for e in sentence_entities if e['label'] in ners])

			if intrasent_relation:
				gold_relations = [ (e1, e2, relation) for e1, e2 , relation in extract_intrasent_goldrelations_from_ann(ann_file, doc = doc ) if e1['label'] == 'Target' and (e2['label'] in ners or (len(ners) == 1 and ners[0] == 'Target'))]
			else:
				gold_relations = [(e1, e2, relation) for e1, e2, relation in extract_gold_relations_from_ann(ann_file) if e1['label'] == 'Target' and (e2['label'] in ners or (len(ners) == 1 and ners[0] == 'Target'))]
			
			if tuple_level:
				inrelation_ids = set([e['std_text'] for e, _ , relation in gold_relations if relation == relation_type] + [e['std_text'] for _ , e, relation in gold_relations if relation == relation_type])

				for e in gold_entities:
					entity_count += 1
					if e['std_text'] in inrelation_ids:
						inrelation_count += 1



			else:
				inrelation_ids = set([(e['doc_start_char'], e['doc_end_char']) for e, _ , relation in gold_relations if relation == relation_type] + [(e['doc_start_char'], e['doc_end_char']) for _ , e, relation in gold_relations if relation == relation_type])
				
				for e in gold_entities:
					entity_count += 1
					if (e['doc_start_char'], e['doc_end_char']) in inrelation_ids:
						inrelation_count += 1

		print(f"Tuple_level:{tuple_level}\nOnly considering entities that cooccur with Target in the same sentence: {entity_cooccur_with_target}")
		print(f"> In {name} SET:\n{inrelation_count}/{entity_count} ({inrelation_count/entity_count*100:.2f}%) entities ({ners}) are in {'intra-sentence' if intrasent_relation else 'intra-sentence and inter-sentence'} {relation_type} relations")

def percentage_of_components_contained_by_multiple_target(train_annfiles, train_corenlpfiles, dev_annfiles, dev_corenlpfiles, relation_type,
	test_annfiles = [], test_corenlpfiles = []):
	for ann_files, corenlp_files, name in zip([train_annfiles, dev_annfiles, test_annfiles], [train_corenlpfiles, dev_corenlpfiles, test_corenlpfiles], ['TRAIN', 'DEV', 'TEST']):
		if len(ann_files) == 0: continue
			
		count_comp_contained = 0
		count_comp_contained_multitar = 0
		for ann_file, corenlp_file in zip(ann_files, corenlp_files):
			comp2tar = {}
			gold_relations = [(e1, e2, relation) for e1, e2, relation in extract_intrasent_goldrelations_from_ann(ann_file, corenlp_file = corenlp_file) if e1['label'] == 'Target' and e2['label'] in ['Element', 'Mineral']]
			for tar, comp, relation in gold_relations:
				comp_id = f"{comp['doc_start_char']},{comp['doc_end_char']}"
				if comp_id not in comp2tar:
					comp2tar[comp_id] = []
				comp2tar[comp_id].append(tar)

			count_comp_contained += len(comp2tar)
			count_comp_contained_multitar += len([comp for comp in comp2tar if len(comp2tar[comp]) > 1])

		print(f"In {name} Set, there are {count_comp_contained} components contained in the same sentence, and {count_comp_contained_multitar}/{count_comp_contained}({count_comp_contained_multitar/count_comp_contained*100:.2f}%) components are contained by multiple target in the same sentence")

def percentage_of_components_contained_by_target(train_annfiles, train_textfiles, train_corenlpfiles, dev_annfiles, dev_textfiles, dev_corenlpfiles, relation_type,
	test_annfiles = [], test_corenlpfiles = [], test_textfiles = []):
	# calculate the percentage of components contained by some target in the same sentence, given there is some target at the same sentence. 
	for ann_files, text_files, corenlp_files, name in zip([train_annfiles, dev_annfiles, test_annfiles], [train_textfiles, dev_textfiles, test_textfiles], [train_corenlpfiles, dev_corenlpfiles, test_corenlpfiles], ['TRAIN', 'DEV', 'TEST']):
		
		if len(ann_files) == 0: continue
		
		count_comp_cooccuring_with_targets = 0
		count_comp_contained_by_targets = 0

		for ann_file, text_file, corenlp_file in zip(ann_files, text_files, corenlp_files):
			gold_relations = [(e1, e2, relation) for e1, e2, relation in extract_intrasent_goldrelations_from_ann(ann_file, corenlp_file = corenlp_file) if e1['label'] == 'Target' and e2['label'] in ['Element', 'Mineral'] and relation == relation_type]

			inrelation_ids = set([(f"{tar['doc_start_char']},{tar['doc_end_char']}", f"{comp['doc_start_char']},{comp['doc_end_char']}") for tar, comp, _ in gold_relations])
			
			comp2tar = {}
			entitypairs = [(e1, e2) for e1, e2 in extract_intrasent_entitypairs_from_text_file(text_file, ann_file, corenlp_file = corenlp_file) if e1['label'] == 'Target' and e2['label'] in ['Element', 'Mineral']]

			for tar, comp in entitypairs:

				comp_id = f"{comp['doc_start_char']},{comp['doc_end_char']}"
				tar_id = f"{tar['doc_start_char']},{tar['doc_end_char']}"

				if comp_id not in comp2tar:
					comp2tar[comp_id] = []
				comp2tar[comp_id].append(tar_id)

			count_comp_cooccuring_with_targets += len(comp2tar)

			for comp_id in comp2tar:
				for tar_id in comp2tar[comp_id]:
					if (tar_id, comp_id) in inrelation_ids:
						count_comp_contained_by_targets += 1
						break

		print(f"In {name} Set, there are {count_comp_cooccuring_with_targets} components occurring with at least one target at the same sentence, and {count_comp_contained_by_targets}/{count_comp_cooccuring_with_targets}({count_comp_contained_by_targets/count_comp_cooccuring_with_targets*100:.2f}%) components are contained by some target in the same sentence")


def percentage_of_components_contained_by_target_across_sentence(train_annfiles, train_textfiles, train_corenlpfiles, dev_annfiles, dev_textfiles, dev_corenlpfiles, relation_type,
	test_annfiles = [], test_corenlpfiles = [], test_textfiles = []):
	# calculate the percentage of components contained by some target across the sentence, given there is some target at the same sentence. 

	for ann_files, text_files, corenlp_files, name in zip([train_annfiles, dev_annfiles, test_annfiles], [train_textfiles, dev_textfiles, test_textfiles], [train_corenlpfiles, dev_corenlpfiles, test_corenlpfiles], ['TRAIN', 'DEV', 'TEST']):
		
		if len(ann_files) == 0: continue
		
		count_comp_cooccuring_with_targets = 0
		count_comp_contained_by_targets_across_sentence = 0

		for ann_file, text_file, corenlp_file in zip(ann_files, text_files, corenlp_files):
			intrasent_gold_relations = [(e1, e2, relation) for e1, e2, relation in extract_intrasent_goldrelations_from_ann(ann_file, corenlp_file = corenlp_file) if e1['label'] == 'Target' and e2['label'] in ['Element', 'Mineral'] and relation == relation_type]
			all_gold_relation_ids = set([(f"{e1['doc_start_char']},{e1['doc_end_char']}", f"{e2['doc_start_char']},{e2['doc_end_char']}") for e1, e2, relation in extract_gold_relations_from_ann(ann_file) if e1['label'] == 'Target' and e2['label'] in ['Element', 'Mineral'] and relation == relation_type])
			intrasent_relation_ids = set([(f"{e1['doc_start_char']},{e1['doc_end_char']}", f"{e2['doc_start_char']},{e2['doc_end_char']}") for e1, e2, relation in intrasent_gold_relations])
			cross_relation_ids = all_gold_relation_ids - intrasent_relation_ids

			cross_contained_compids = set([comp_id for _, comp_id in cross_relation_ids])

			entitypairs = [(e1, e2) for e1, e2 in extract_intrasent_entitypairs_from_text_file(text_file, ann_file, corenlp_file = corenlp_file) if e1['label'] == 'Target' and e2['label'] in ['Element', 'Mineral']]
			compid2tarid = {}
			for tar, comp in entitypairs:
				comp_id = f"{comp['doc_start_char']},{comp['doc_end_char']}"
				tar_id = f"{tar['doc_start_char']},{tar['doc_end_char']}"
				if comp_id not in compid2tarid:
					compid2tarid[comp_id] = []
				compid2tarid[comp_id].append(tar_id)

			count_comp_cooccuring_with_targets += len(compid2tarid)

			for comp_id in compid2tarid:
				if comp_id not in cross_contained_compids:
					continue	
				insent_contained = 0 
				for tar_id in compid2tarid[comp_id]:
					if (tar_id, comp_id) in intrasent_relation_ids:
						insent_contained = 1
						break
				if not insent_contained:
					count_comp_contained_by_targets_across_sentence += 1

		print(f"In {name} Set, there are {count_comp_cooccuring_with_targets} components cooccurring with some targets in the same sentence, and {count_comp_contained_by_targets_across_sentence}/{count_comp_cooccuring_with_targets}({count_comp_contained_by_targets_across_sentence/count_comp_cooccuring_with_targets*100:.2f}%) of them are contained by only targets across sentences")

def percentage_of_wider_entities_have_smaller_entities(train_annfiles, train_textfiles, train_corenlpfiles, dev_annfiles, dev_textfiles, dev_corenlpfiles, relation_type, test_annfiles = [], test_textfiles = [], test_corenlpfiles = []):
	# number of nested components in relation / number of nested components
	wider_labeled_as_nested = 0 # wider entities that also have its smaller parts labeled as entitie
	wider = 0  # entities that potentially have sub entities
	wider_texts = set()
	for ann_files, text_files, corenlp_files, name in zip([train_annfiles, dev_annfiles, test_annfiles], [train_textfiles, dev_textfiles, test_textfiles], [train_corenlpfiles, dev_corenlpfiles, test_corenlpfiles], ['TRAIN', 'DEV', 'TEST']):
		
		if len(ann_files) == 0: continue
		
		

		for ann_file, text_file, corenlp_file in zip(ann_files, text_files, corenlp_files):

			gold_entities = [e for e in extract_gold_entities_from_ann(ann_file) if e['label'] in ['Element', 'Mineral']]

			offset2allcomps = {}
			offset2text = {}

			for e in gold_entities:
				curstart, curend = e['doc_start_char'], e['doc_end_char']
				offset2text[(curstart, curend)] = e['text']
				is_inside = 0 
				for start, end in offset2allcomps:
					if start <= curstart < curend <= end:
						is_inside = 1
						offset2allcomps[(start,end)].append((curstart, curend))

				if not is_inside:
					offset2allcomps[(curstart, curend)] = [(curstart, curend)]

			for start,end in offset2allcomps:
				comps = offset2allcomps[(start,end)]
				text = offset2text[(start, end)]
				wider += 1 if len(text.strip().split()) > 1 or "_" in text or "-" in text else 0
				wider_labeled_as_nested += 1 if len(comps) > 1 else 0 
				if len(text.strip().split()) > 1 or "_" in text or "-" in text:
					wider_texts.add(text)
	print(f"There are {wider} wider entities that contain space or hyphens, and {wider_labeled_as_nested} of them are have smaller entities annotated")
	print(wider_texts)




def preceding_and_following(train_annfiles, train_textfiles, train_corenlpfiles, dev_annfiles, dev_textfiles, dev_corenlpfiles, relation_type, test_annfiles = [], test_textfiles = [], test_corenlpfiles = []):
	# number of nested components in relation / number of nested components
	
	for ann_files, text_files, corenlp_files, name in zip([train_annfiles, dev_annfiles, test_annfiles], [train_textfiles, dev_textfiles, test_textfiles], [train_corenlpfiles, dev_corenlpfiles, test_corenlpfiles], ['TRAIN', 'DEV', 'TEST']):
		
		if len(ann_files) == 0: continue
		count_preceding = 0
		count_following = 0
		for ann_file, text_file, corenlp_file in zip(ann_files, text_files, corenlp_files):


			intrasent_gold_relations = [(e1, e2, relation) for e1, e2, relation in extract_intrasent_goldrelations_from_ann(ann_file, corenlp_file = corenlp_file) if e1['label'] == 'Target' and e2['label'] in ['Element', 'Mineral'] and relation == relation_type]

			for e1, e2, relation in intrasent_gold_relations:
				if e1['doc_start_char'] < e2['doc_end_char']:
					count_preceding += 1
				else:
					count_following += 1
		print(f"{count_preceding} relations have targets preceding component, and {count_following} relations have component preceding targets")



def main():
	train_annfiles, train_textfiles, train_corenlpfiles, dev_annfiles, dev_textfiles, dev_corenlpfiles, test_annfiles, test_textfiles, test_corenlpfiles = load_files()



	ners = ['Element', 'Mineral']
	relation_type = 'Contains'
	intrasent_relation = False
	entity_cooccur_with_target = True
	tuple_level = True
	# percentage_entities_in_relation(train_annfiles, train_corenlpfiles, dev_annfiles, dev_corenlpfiles, ners, relation_type, intrasent_relation = intrasent_relation, entity_cooccur_with_target = entity_cooccur_with_target, tuple_level = tuple_level)

	# percentage_of_components_contained_by_multiple_target(train_annfiles, train_corenlpfiles, dev_annfiles, dev_corenlpfiles, relation_type)

	# percentage_of_components_contained_by_target(train_annfiles, train_textfiles, train_corenlpfiles, dev_annfiles, dev_textfiles, dev_corenlpfiles, relation_type)

	# percentage_of_components_contained_by_target_across_sentence(train_annfiles, train_textfiles, train_corenlpfiles, dev_annfiles, dev_textfiles, dev_corenlpfiles, relation_type)

	# percentage_of_smaller_entities_being_in_relation(train_annfiles, train_textfiles, train_corenlpfiles, dev_annfiles, dev_textfiles, dev_corenlpfiles, relation_type)

	# percentage_of_wider_entities_have_smaller_entities(train_annfiles, train_textfiles, train_corenlpfiles, dev_annfiles, dev_textfiles, dev_corenlpfiles, relation_type, test_annfiles = test_annfiles, test_textfiles = test_textfiles, test_corenlpfiles = test_corenlpfiles)

	preceding_and_following(train_annfiles, train_textfiles, train_corenlpfiles, dev_annfiles, dev_textfiles, dev_corenlpfiles, relation_type)



if __name__ == "__main__":
	main()
