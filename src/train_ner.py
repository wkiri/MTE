#!/usr/bin/env python
# Train a NER model using specified documents and gazette file,
# then save it to the specified model file.
#
# Kiri Wagstaff
# July 27, 2021
import os
import sys
from brat2ner_bulkdoc_multiword import BratToNerConverter


def main(doc_file, gazette_file, model_file):

    # Check arguments
    for f in [doc_file, gazette_file]:
        if not os.path.exists(f):
            print('Could not find %s' % f)
            sys.exit(1)

    # If needed, generate .tsv file for CoreNLP
    tsv_file = os.path.splitext(doc_file)[0] + '.tsv'
    if not os.path.exists(tsv_file):
        print('Generating .tsv file... ')
        # Redirect stdout to a log file
        tsv_log = tsv_file + '.log'
        stdout_save = sys.stdout
        sys.stdout = open(tsv_log, 'w')
        br = BratToNerConverter()
        br.convert_all(doc_file, tsv_file)
        # restore stdout
        sys.stdout = stdout_save
        print(' Saved to %s, logged to %s' % (tsv_file, tsv_log))

    # Train the CoreNLP model


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(argument_default=argparse.SUPPRESS, 
                                     description='Train and save NER model.')

    parser.add_argument('doc_file', help='Text file (.list) with one line per document with location of .txt and .ann files')
    parser.add_argument('gazette_file', help='Gazette (.gaz.txt) with entity types and names')
    parser.add_argument('model_file', help='Model file (.ser.gz) to save trained NER model')

    args = parser.parse_args()
    main(**vars(args))
