
# pure can't find but g5 can 
pures = set(["\n".join(k.strip().split("\n")[:5]) for k in open(f"./pure_test_cases/false_negatives.txt").read().split("\n\n") if k.strip() != ""])
g5s = set(["\n".join(k.strip().split("\n")[:5]) for k in open(f"./G5_analysis/true_positives.txt").read().split("\n\n") if k.strip() != ""])
for l in list(pures.intersection(g5s)):
	print(l)
	print()


