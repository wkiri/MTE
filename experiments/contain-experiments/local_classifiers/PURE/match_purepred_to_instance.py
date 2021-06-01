# author: Yuan Zhuang 
# This code maps pure prediction back to span_instance and rel_instance such that evaluation is eaiser
import re, pickle, sys, argparse, random, json, os
from copy import deepcopy 
from sys import stdout 
from os.path import abspath, dirname, join, exists
from os import makedirs, listdir
from transformers import *

curpath = dirname(abspath(__file__))
upperpath = dirname(curpath)
sys.path.append(upperpath)
from instance import Span_Instance, Rel_Instance

parentpath = dirname(upperpath)
sys.path.insert(0, parentpath)
from extraction_utils import get_docid, extract_gold_entities_from_ann,extract_intrasent_entitypairs_from_text_file, extract_intrasent_goldrelations_from_ann, extract_entities_from_text, get_offset2sentid, get_sentid_from_offset

label2id = {label:i for i, label in enumerate(json.load(open("./temp/rel/label_list.json", "r")))}
id2label = {i:label for i, label in label2id.items()}

def find_doc_offset(tokens, tok_sidx, tok_eidx):
	# given a token of star idx and end idx, find its token offset in doc 
	start_char = -1
	end_char = -1 

	for i, tok in enumerate(tokens):
		if i == tok_sidx and start_char == -1:
			start_char = tok['characterOffsetBegin']
		if i == tok_eidx and end_char == -1:
			end_char = tok['characterOffsetEnd']
	assert start_char != -1 and end_char != -1
	return start_char, end_char


def main():
	outfile = "./temp/rel/predictions.pkl"
	corenlp_dir = "../../../../parse/"
	ann_dir = "../../../../corpus-LPSC"
	
	relins = [] # store prediction instances
	
	# load predictions 
	predicted_docs = []
	for line in open("./temp/rel/predictions.json", "r").read().strip().split("\n"):
		predicted_docs.append(json.loads(line))

	for docidx, predicted_doc in enumerate(predicted_docs):

		venue, year, docname = predicted_doc['doc_key'].split(',')

		if "lpsc" in venue:
			doc = json.load(open(join(corenlp_dir, venue, docname + ".txt.json"), "r"))
			ann_file = join(ann_dir,venue, docname + ".ann")
			text_file = join(ann_dir,venue, docname + ".txt")
		else:
			doc = json.load(open(join(corenlp_dir, venue, f"{year}_{docname}.txt.json"), "r"))
			ann_file = join(ann_dir,venue, f"{year}_{docname}.ann")
			text_file = join(ann_dir,venue, f"{year}_{docname}.txt")

		# get offset to ner label 
		gold_entities = [e for e in extract_gold_entities_from_ann(ann_file) if e['label'] in ['Target', 'Element', 'Mineral']]
		offset2ner = {}
		for e in gold_entities:
			offset2ner[(e['doc_start_char'], e['doc_end_char'])]= e['label'] if e['label'] == 'Target' else 'Component' 

		for sentid, sent_relations in enumerate(predicted_doc['predicted_relations']):
			
			cumu_toks = sum([len(doc['sentences'][s]['tokens']) for s in range(sentid)])

			for tok_sidx1, tok_eidx1, tok_sidx2, tok_eidx2, logit, relation in sent_relations: # eidx is inclusive
				tok_sidx1, tok_eidx1, tok_sidx2, tok_eidx2 = tok_sidx1 -cumu_toks, tok_eidx1-cumu_toks, tok_sidx2-cumu_toks, tok_eidx2-cumu_toks

				tokens = doc['sentences'][sentid]['tokens']

				tok1_doc_start_char, tok1_doc_end_char = find_doc_offset(tokens, tok_sidx1 , tok_eidx1)
				
				tok2_doc_start_char, tok2_doc_end_char = find_doc_offset(tokens, tok_sidx2 , tok_eidx2)
				
				ner1 = offset2ner.get((tok1_doc_start_char, tok1_doc_end_char), "")

				ner2 = offset2ner.get((tok2_doc_start_char, tok2_doc_end_char), "")
				
				if ner1 != "Target" or ner2 != 'Component':
					continue

				text1 = " ".join([t['word'] for t in tokens[tok_sidx1: tok_eidx1 + 1]])
				text2 = " ".join([t['word'] for t in tokens[tok_sidx2: tok_eidx2 + 1]])


				span1 = Span_Instance(venue, year, docname, tok1_doc_start_char, tok1_doc_end_char, text1, ner1 )

				span2 = Span_Instance(venue, year, docname, tok2_doc_start_char, tok2_doc_end_char, text2, ner2 )

				rel = Rel_Instance(span1, span2)
				rel.pred_relation_label = relation
				relins.append(rel)

	print(f"{len(relins)} in predictions, {len([rel for rel in relins if rel.pred_relation_label == 'Contains'])} Contains and {len([rel for rel in relins if rel.pred_relation_label == 'O'])} O's")
	print(f"saving converted prediction file to {outfile}")
	with open(outfile, "wb") as f:
		pickle.dump(relins, f)

if __name__ == "__main__":
	main()
		