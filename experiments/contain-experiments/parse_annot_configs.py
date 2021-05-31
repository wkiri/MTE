# this file contains the configs over the relations and labels. This is used for parsing the annotation files and constrains what targets and relations would be used and validate over in the experiments

# ---------- TO MODIFY ---------------
accept_ner_labels = [
	"Element", 
	"Mineral", 
	"Target"]

accept_entityrelations = set([
		"Target-Mineral:Contains",
		"Target-Element:Contains",
		])
tokenizer_type = "bert-base-uncased"

# ------- automated part. Do not modify -----------
ner_label2ind = {l: i for i, l in enumerate(sorted(accept_ner_labels))}
ner_label2ind["O"] = len(ner_label2ind)

ner_ind2label = {i: l for l, i in ner_label2ind.items()}


relation_label2ind = {}
for i, l in enumerate(sorted(accept_entityrelations)):
 	l = l.split(":")[1]
 	if l in relation_label2ind:
 		continue
 	relation_label2ind[l] = len(relation_label2ind)
relation_label2ind["O"] = len(relation_label2ind)

relation_ind2label = {i:l for l, i in relation_label2ind.items()}

accept_subject2object = {}
for relation in accept_entityrelations:
	subject, obj = relation.split("-")
	obj, rel = obj.split(":")
	if subject not in accept_subject2object:
		accept_subject2object[subject] = {}
	assert obj not in accept_subject2object[subject]
	accept_subject2object[subject][obj] = rel

ner2typemarker = {}
seen_typemarker = set()
for l in ner_label2ind:
	tm = l[0] + l[-1]
	assert tm not in seen_typemarker

	ner2typemarker[l] = tm
	seen_typemarker.add(tm)


