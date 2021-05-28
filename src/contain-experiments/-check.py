import glob
from os.path import join
labels = set(["Element", "Target", "Mineral"]) 
def check_ners(indir):

	for file in sorted(glob.glob(join(indir, "*.ann"))):
		counts = {l:0 for l in labels}

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
		print(file)
		print(counts)
		# if file == "/uusoc/res/nlp/nlp/yuan/mars/data/corpus-LPSC/lpsc15-C-raymond-sol1159-v3-utf8/1438.ann":
			# print("\n".join(sorted(ners, key = lambda x: int(x[1:]))))
check_ners("/uusoc/res/nlp/nlp/yuan/mars/data/corpus-LPSC/lpsc15")