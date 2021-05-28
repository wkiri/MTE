jsre_instance_file = "../../jsre-contains-exp/temp/tuples.txt"
pure_instance_file = "temp/instances.txt"

jsre_tuples = set()
with open(jsre_instance_file, "r") as f:
	lines = [line.split(",") for line in f.read().strip().split("\n")]

	for venue, year, docname, std1, std2 in lines:
		jsre_tuples.add((venue.strip(), year.strip(), docname.strip(), std1.strip(), std2.strip()))

pure_instances = set()
with open(pure_instance_file, "r" ) as f:
	lines = [line.split(",") for line in f.read().strip().split("\n")]
	print(lines[0])
	for venue, year, docname,orgtext1, orgtex2, std1, std2 in lines:
		pure_instances.add((venue.strip(), year.strip(), docname.strip(), std1.strip(), std2.strip(), orgtext1.strip(), orgtex2.strip()))
puretuple2prgtext = {}

for venue, year, docname, std1, std2, org1, org2 in pure_instances:
	if (venue, year, docname, std1, std2) not in puretuple2prgtext:
		puretuple2prgtext[(venue, year, docname, std1, std2)] = []
	puretuple2prgtext[(venue, year, docname, std1, std2)].append((org1, org2))

for (venue, year, docname, std1, std2) in sorted(jsre_tuples):
	if (venue, year, docname, std1, std2) not in puretuple2prgtext:
		print((venue, year, docname, std1, std2))
