import glob 
def parse(txt_file, ann_file, accept_entities):
    has_error = 0 
    with open(txt_file) as text_file, open(ann_file) as ann_file:
        texts = text_file.read().decode('utf8')
        text_file.close()
        anns = map(lambda x: x.strip().split('\t'), ann_file)
        anns = filter(lambda x: len(x) > 2, anns)
        # FIXME: ignoring the annotations which are complex

        anns = filter(lambda x: ';' not in x[1], anns)

        # FIXME: some annotations' spread have been split into many, separated by ; ignoring them

        def __parse_ann(ann):
            spec = ann[1].split()
            entity_type = spec[0]
            ann_id = ann[0]
            markers = list(map(lambda x: int(x), spec[1:]))
            # t = ' '.join([texts[begin:end] for begin,end in zip(markers[::2], markers[1::2])])
            t = texts[markers[0]:markers[1]]
            if not t == ann[2]:
                print("Error: Annotation mis-match, file=%s, ann=%s, text=%s" % (txt_file, str(ann), t))
                has_error = 1
                return None
            return (entity_type, markers, t, ann_id)

        anns = map(__parse_ann, anns)  # format
        anns = filter(lambda x: x, anns)  # skip None

        # building a tree index for easy accessing
        tree = {}
        for entity_type, pos, name, ann_id in anns:
            if entity_type in accept_entities:
                begin, end = pos[0], pos[1]
                if begin not in tree:
                    tree[begin] = {}
                node = tree[begin]
                if end not in node:
                    node[end] = []
                node[end].append(ann_id)

        # Re-read file in without decoding it
        text_file = open(txt_file)
        texts = text_file.read()
        text_file.close()
        return texts, tree, has_error



accept_entities = {"Target", "Element", "Mineral"}

error_files = []
for txt_file in glob.glob("/proj/mte/results/phx-reviewed+properties-v2/*.txt"):
    
    ann_file = txt_file.split(".txt")[0] + ".ann"
    texts, tree, has_error = parse(txt_file, ann_file, accept_entities)

    if has_error:
        error_files.append(txt_file)

print(">>> files that have errors")
print("\n".join(error_files))