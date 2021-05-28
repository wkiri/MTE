import sys 
infile = sys.argv[1]
outfile = sys.argv[2]


with open(infile, "r") as f:
	lines = f.read().strip().split("\n")

with open(outfile, "w") as f:
	for line in lines:
		items = line.split("\t")
		label = int(items[0])
		label = "1" if label > 0 else "0"
		f.write("\t".join([label] + items[1:]) + "\n")
