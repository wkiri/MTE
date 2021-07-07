#!/usr/bin/env python3
# Read in brat .ann files and convert to CoreNLP's NER CRF format.
#
# Author: Steven Lu
# Copyright notice at bottom of file.

from pycorenlp import StanfordCoreNLP
import os, re
from argparse import ArgumentParser
import sys
reload(sys)  # Reload does the trick!
sys.setdefaultencoding('UTF8')
import urllib 

#accept_labels = set(['Element', 'Mineral', 'Target', 'Material', 'Locality', 'Site'])
accept_labels = set(['Element', 'Mineral', 'Target'])
#accept_labels = set(['Target'])


def get_docid(ann_file):
    venue = ann_file.split("/")[-2]
    if "lpsc" in ann_file:
        year = re.findall(r"lpsc(\d+)", ann_file)[0]
        docname = ann_file.split("/")[-1].split(".")[0]
    elif "mpf" in ann_file or "phx" in ann_file:
        year, docname = re.findall(r"(\d+)_(\d+)", ann_file.split("/")[-1])[0] 
    else:
        raise NameError("file must be from LPSC or MPF or PHX. Currently we have  %s" % (ann_file))
    return venue, year, docname


class BratToNerConverter(object):
    def __init__(self, corenlp_url='http://localhost:9000'):
        '''
        Create Converter for converting brat annotations to Core NLP NER CRF
        classifier training data.

        To start the server checkout: http://stanfordnlp.github.io/CoreNLP/corenlp-server.html#getting-started
        '''
        self.corenlp = StanfordCoreNLP(corenlp_url)


    def convert(self, text_file, ann_file):
        text, tree = self.parse(text_file, ann_file)
        props = { 'annotators': 'tokenize,ssplit', 'outputFormat': 'json'}
        if text[0].isspace():
            text = '.' + text[1:]
            # Reason: some tools trim/strip off the white spaces
            # which will mismatch the character offsets
        print(text_file)
        # added by yuan 
        venue, year, docname = get_docid(ann_file)
        if sys.version[0] == '2':
            # use urllib to escape the percentage symbol. otherwise it could cause error in corenlp which says 'cannot handle incoming annotation'
            text = urllib.quote(text)
        output = self.corenlp.annotate(text, properties=props)
        records = []
        for sentence in output['sentences']:
            continue_ann, continue_ann_en = None, None
            sentid = sentence['index']
            for tok in sentence['tokens']:
                begin, tok_end = tok['characterOffsetBegin'], tok['characterOffsetEnd']
                doc_start_char, doc_end_char = begin, tok_end
                label = 'O'
                if begin in tree:
                    node = tree[begin]
                    if len(node) > 1:
                        print("WARN: multiple starts at ", begin, node)
                        if tok_end in node:
                            node = {tok_end: node[tok_end]} # picking one
                            print("Chose:", node)
                                                
                    ann_end, labels = node.items()[0]
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
                yield "%s\t%s" % (tok['word'], label), "%s\t%s\t%s\t%d\t%d\t%d" % (venue, year, docname, sentid, doc_start_char, doc_end_char)
            #yield "" # end of sentence
        yield "", "" # end of document


    def parse(self, txt_file, ann_file):
        with open(txt_file) as text_file, open(ann_file) as ann_file:
            texts = text_file.read().decode('utf8') 
            text_file.close()
            #texts = text_file.read()
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

    def convert_all(self, input_paths, output):
        tracking_output = output + ".track"

        with open(input_paths) as paths, open(output, 'w') as out, open(tracking_output, 'w') as trackf:
            for p in map(lambda x: x.strip(), paths):
                d = p.split(',')
                for line, track_line in self.convert(d[0], d[1]):
                    out.write(line)
                    out.write("\n")

                    trackf.write(track_line)
                    trackf.write("\n")
                out.write("\n") # end of document
                trackf.write('\n')

if __name__ == '__main__':

    parser = ArgumentParser(description="Brat to CoreNLP NER annotation converter")
    parser.add_argument("--in", help="""Input file, each line contains comma separated *.txt,*.ann\n
    To create the input file, follow these instructuions:
    $ ls $PWD/*.txt > 1.list
    $ ls $PWD/*.ann > 2.list
    $ paste  -d "," 1.list  2.list  > input.list""", required=True)
    parser.add_argument("--out", help="""Output file""", required=True)
    parser.add_argument("--port", help="""corenlp port""", default = 9000, type = int)
    args = vars(parser.parse_args())
    corenlp_url = "http://localhost:%s" %(args['port'])
    BratToNerConverter(corenlp_url = corenlp_url).convert_all(args['in'], args['out'])

# Copyright 2017, by the California Institute of Technology. ALL
# RIGHTS RESERVED. United States Government Sponsorship
# acknowledged. Any commercial use must be negotiated with the Office
# of Technology Transfer at the California Institute of Technology.
#
# This software may be subject to U.S. export control laws and
# regulations.  By accepting this document, the user agrees to comply
# with all applicable U.S. export laws and regulations.  User has the
# responsibility to obtain export licenses, or other export authority
# as may be required before exporting such information to foreign
# countries or providing access to foreign persons.

