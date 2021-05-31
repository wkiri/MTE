# This is to replicate the all-yes-baseline in Table 4.
import glob

# =============TO modify =============== 
t ="mineral"
# ======================= do NOT modify ==============
files = glob.glob("/home/yzhuang/mars/experiments/jsre/iaai/test-%s/*.examples" % (t))

labels = []
for file in files:
	with open(file, "r") as f:
		for line in f.read().strip().split("\n"):
			if line.strip() == "": continue
			label = int(line.split("\t")[0])
			labels.append(label > 0) # there are some labels that are not binary (e.g. 2 in the first line of 2145-element.examples). here we treat them as binary 

num_correct = sum(labels)
recall = 1
precision = num_correct * 1.0 / len(labels)
f1 = 2 * recall * precision/(recall + precision)
print("precision: %s, recall: %s, f1: %s" % (str(precision), str(recall), str(f1))) 