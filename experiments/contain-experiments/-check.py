import glob
from os.path import join
labels = set(["Element", "Target", "Mineral"]) 
def check_ners(indir):
	counts = {l:0 for l in labels}

	for file in sorted(glob.glob(join(indir, "*.ann"))):

		seen_ner = set()
		ners = []
		with open(file, "r") as f:
			for k in f.readlines():
				k = k.strip()
				if len(k.split("\t")) == 3:
					
					annot_id, ner, text = k.split("\t")
					if ner in seen_ner: continue
					seen_ner.add(ner)
					ner, start, end = ner.split()
					if annot_id[0] == "T" and ner in labels:
						counts[ner] += 1
						if ner == "Element" or ner == "Mineral":
							ners.append(annot_id)

	print(counts)
check_ners("../../corpus-LPSC/lpsc15-C-raymond-sol1159-v3-utf8")