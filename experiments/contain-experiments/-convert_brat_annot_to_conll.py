#!/usr/bin/env python3
# Read in brat .ann files and convert to CoreNLP's NER CRF format.
#
# Author: Steven Lu
# Copyright notice at bottom of file.

# from pycorenlp import StanfordCoreNLP
import os, sys, argparse, json, re
from os import makedirs, listdir
from os.path import exists, join, abspath
from sys import stdout

from parse_annot_configs import accept_ner_labels as accept_labels

class BratToNerConverter(object):
    # def __init__(self, corenlp_url='http://localhost:9000'):
    #     '''
    #     Create Converter for converting brat annotations to Core NLP NER CRF
    #     classifier training data.

    #     To start the server checkout: http://stanfordnlp.github.io/CoreNLP/corenlp-server.html#getting-started
    #     '''
    #     # self.corenlp = StanfordCoreNLP(corenlp_url)
    #     self.corenlp = None # only tokenize

    def __init__(self):
        pass

    def convert(self, text_file, ann_file, stanford_file, stanford_has_ner_prediction):


        # if self.corenlp is None:
        #     self.corenlp = stanza.Pipeline('en', processors='tokenize')

        print(text_file, ann_file)
        text, tree = self.parse(text_file, ann_file)
        # props = { 'annotators': 'tokenize,ssplit', 'outputFormat': 'json'}
        # if text[0].isspace():
        #     text = '.' + text[1:]
        #     # Reason: some tools trim/strip off the white spaces
        #     # which will mismatch the character offsets
        # # output = self.corenlp.annotate(text, properties=props) # error here

        # output = self.corenlp(text)
        output = json.load(open(stanford_file, "r"))

        records = []
        # for sentence in output['sentences']:
        for sentid, sentence in enumerate(output["sentences"]):
            continue_ann, continue_ann_en = None, None
            # for tok in sentence['tokens']:
            for tok in sentence["tokens"]:
                # begin, tok_end = tok['characterOffsetBegin'], tok['characterOffsetEnd']
                begin, tok_end = tok["characterOffsetBegin"], tok["characterOffsetEnd"]
                label = 'O' # annotated ner label
                if stanford_has_ner_prediction:
                    predicted_ner = tok["ner"] if tok["ner"] in accept_labels else "O" # predicted ner label from trained ner model

                if begin in tree:
                    node = tree[begin]
                    if len(node) > 1:
                        print("WARN: multiple starts at ", begin, node)
                        if tok_end in node:
                            node = {tok_end: node[tok_end]} # picking one
                            print("Chose:", node)
                    
                    ann_end, labels = list(node.items())[0]
                    if not len(labels) == 1:
                        print("WARN: Duplicate labels for token: %s, label:%s. Using the first one!" % (tok['word'], str(labels)))
                    if accept_labels is not None and labels[0] in accept_labels:
                        label = labels[0]
                    if tok_end == ann_end: # annotation ends where token ends
                        continue_ann = None
                    elif tok_end < ann_end and label != 'O':
                        print("Continue for the next %d chars" % (ann_end - tok_end))
                        continue_ann = label
                        continue_ann_end = ann_end
                elif continue_ann is not None and tok_end <= continue_ann_end:
                    print("Continuing the annotation %s, %d:%d %d]" % (continue_ann, begin, tok_end, continue_ann_end))
                    label = continue_ann            # previous label is this label
                    if continue_ann_end == tok_end: # continuation ends here
                        print("End")
                        continue_ann = None
                if stanford_has_ner_prediction:
                    yield f"{tok['word']}\t{tok['lemma']}\t{label}\t{predicted_ner}\t{tok['characterOffsetBegin']}\t{tok['characterOffsetEnd']}\t{1 if continue_ann is not None else 0}"
                else:
                    yield f"{tok['word']}\t{label}\t{tok['characterOffsetBegin']}\t{tok['characterOffsetEnd']}\t{1 if continue_ann is not None else 0}"
            yield f"sentid={sentid}\n"
            #yield "" # end of sentence
        yield "" # end of document


    def parse(self, txt_file, ann_file):
        with open(txt_file) as text_file, open(ann_file) as ann_file:
            texts = text_file.read()
            text_file.close()

            anns = map(lambda x: x.strip().split('\t'), ann_file)
            anns = filter(lambda x: len(x) > 2, anns)
            # FIXME: ignoring the annotatiosn which are complex

            anns = filter(lambda x: ';' not in x[1], anns)
            # FIXME: some annotations' spread have been split into many, separated by ; ignoring them

            def __parse_ann(ann):
                spec = ann[1].split()
                name = spec[0]
                markers = list(map(lambda x: int(x), spec[1:]))
                #t = ' '.join([texts[begin:end] for begin,end in zip(markers[::2], markers[1::2])])
                t = texts[markers[0]:markers[1]]
                if not t == ann[2]:
                    print("Error: Annotation mis-match, file=%s, ann=%s" % (txt_file, str(ann)))
                    return None
                return (name, markers, t)
            anns = map(__parse_ann, anns) # format
            anns = filter(lambda x: x, anns) # skip None

            # building a tree index for easy accessing
            tree = {}
            for entity_type, pos, name in anns:
                begin, end = pos[0], pos[1]
                if begin not in tree:
                    tree[begin] = {}
                node = tree[begin]
                if end not in node:
                    node[end] = []
                node[end].append(entity_type)

            # Re-read file in without decoding it
            text_file = open(txt_file)
            texts = text_file.read()
            text_file.close()
            return texts, tree

    def convert_all(self, input_dirs, stanford_dirs, temp_output_dir, stanford_has_ner_prediction):
        assert len(input_dirs)  == len(stanford_dirs)

        # make sure that the directory names (such as lpsc15..) in stanford_dirs should match the ones of the corresponding input_dirs
        assert all([indir.strip("/").split("/")[-1] == stanford_dir.strip("/").split("/")[-1] for indir, stanford_dir in zip(input_dirs, stanford_dirs)])

        for indir, stanford_dir in zip(input_dirs, stanford_dirs):
            venue = indir.strip("/").split("/")[-1]
            outdir = join(temp_output_dir, venue)
            if not exists(outdir): 
                makedirs(outdir)

            text_files = [join(indir, file) for file in listdir(indir) if file.endswith(".txt")]
            ann_files = [join(indir, file.split(".txt")[0] + ".ann") for file in listdir(indir) if file.endswith(".txt")] 
            stanford_files = [join(stanford_dir, file + ".json") for file in listdir(indir) if file.endswith(".txt")] 

            assert len(stanford_files) == len(ann_files) == len(text_files)

            for i, (text_file, ann_file,stanford_file) in enumerate(zip(text_files, ann_files, stanford_files)):
                stdout.write(f"\rParsing {i+1}/{len(text_files)} files from {indir}")
                stdout.flush()

                if "mpf-" in text_file or "phx-" in text_file: # only a subset of these datasets that contain at least 1 target and 1 component are parsed. check for more details in parse_text_files_with_ner.py  
                    if not exists(stanford_file):
                        continue


                filename = text_file.split("/")[-1].split(".txt")[0] + ".txt"

                with open(join(outdir, filename), "w") as out:
                    for line in self.convert(text_file, ann_file, stanford_file, stanford_has_ner_prediction):
                        out.write(line)
                        out.write("\n")
                    out.write("\n") # end of document
    

# making files for trainining ner model:
# python convert_brat_annot.py --indir ../data/corpus-LPSC/lpsc15-C-raymond-sol1159-v3-utf8 ../data/corpus-LPSC/lpsc16-C-raymond-sol1159-utf8 --outdir ../data/converted/corpus-LPSC/lpsc15-C-raymond-sol1159-v3-utf8 ../data/converted/corpus-LPSC/lpsc16-C-raymond-sol1159-utf8 --stanford_dirs ../data/stanford-parse/corpus-LPSC/lpsc15-C-raymond-sol1159-v3-utf8 ../data/stanford-parse/corpus-LPSC/lpsc16-C-raymond-sol1159-utf8

# # making files for training re model: 
# python convert_brat_annot.py --indir ../data/corpus-LPSC/lpsc15-C-raymond-sol1159-v3-utf8 ../data/corpus-LPSC/lpsc16-C-raymond-sol1159-utf8 --outdir ../data/converted/corpus-LPSC-with-ner --stanford_has_ner_prediction 1
if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='use stanford corenlp to parse text file')
    parser.add_argument('--indir', nargs="+", required = True, help="directories that contains .txt files")

    parser.add_argument('--stanford_dirs', nargs="+", required = True, help="directories that contains .txt.json files")

    parser.add_argument('--stanford_has_ner_prediction', default = 0, type = int, choices = [1,0], help="whether the stanford parse file contains ner predictions from the trained ner model. this should be false when making files for training ner model, and should be true when making files for training relation extraction model")

    parser.add_argument('--outdir', required = True, help="output directory")

    args = parser.parse_args()

    BratToNerConverter().convert_all(args.indir,args.stanford_dirs , args.outdir, args.stanford_has_ner_prediction)

