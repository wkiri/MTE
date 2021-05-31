def read(ann_file):
    with open(annfile,"r") as f:
        lines = [k for k in f.read().strip().split("\n") if k.strip() != ""]

    contain_relations = []
    allowed_ners = set(["Target", "Element", "Mineral"])
    annotid2nertype = {}
    for linenum, annotation_line in enumerate(lines):
        #annotation_id, markup, name = annotation_line.strip().split('\t')
        splitline = annotation_line.strip().split('\t')

        name = splitline[0]
        if name[0] == "T":
            annotid = splitline[0]
            label   = splitline[1].split()[0]
            args         = splitline[1].split()[1:]
            start   = args[0]
            end     = args[-1]
            text    = splitline[2]
            if label in allowed_ners:
                annotid2nertype[annotid] = label
        elif name[0] == 'E': # event
            print("EVENT! ")
            print(f"Line: {annotation_line}")
            args         = splitline[1].split() 
            label   = args[0].split(':')[0]
            anchor  = args[0].split(':')[1]
            args         = [a.split(':') for a in args[1:]]
            targets = [v for (t,v) in args if t.startswith('Targ')]
            cont    = [v for (t,v) in args if t.startswith('Cont')]
            if label == "Contains":
                for t in targets: 
                    for c in cont:
                        print(f"   adding {t}->{c} ")
                        contain_relations.append((t,c))
    # # filter by ner type 
    # contain_relations = [(t,c) for t, c in contain_relations if t in annotid2nertype and c in annotid2nertype and annotid2nertype[t] == "Target" and (annotid2nertype[c] == "Element" or annotid2nertype[c] == "Mineral")]

    count_element = len([a for a in annotid2nertype if annotid2nertype[a] == "Element"])

    count_target = len([a for a in annotid2nertype if annotid2nertype[a] == "Target"])

    count_mineral = len([a for a in annotid2nertype if annotid2nertype[a] == "Mineral"])
    return contain_relations, count_element, count_target, count_mineral 


contain_relations = []
count_element = 0
count_target = 0
count_mineral = 0
import glob 
# annfiles = glob.glob("../../data/corpus-LPSC/lpsc15-C-raymond-sol1159-v3-utf8/*.ann")

annfiles = glob.glob("../../data/corpus-LPSC/lpsc16-C-raymond-sol1159-utf8/*.ann")
for annfile in annfiles:
    items = read(annfile)
    contain_relations.extend(items[0])
    count_element += items[1]
    count_mineral += items[-1]
    count_target += items[2]

print(len(contain_relations), count_element, count_target, count_mineral)