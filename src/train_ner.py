#!/usr/bin/env python
# Train a NER model using specified documents and CoreNLP properties file,
# then save it to the specified model file.
#
# Kiri Wagstaff
# July 27, 2021
import os
import sys
import subprocess
from brat2ner_bulkdoc_multiword import BratToNerConverter
corenlp = '/proj/mte/stanford-corenlp-mte-4.2.0'


# Using CoreNLP TSV file, 
# train a CoreNLP NER model with the generic properties
# in corenlp_file and custom gazette_file,
# then save result to model_file
def train_ner(tsv_file, corenlp_file, gazette_file, model_file):

    custom_args = '-trainFile %s ' % tsv_file
    custom_args += '-gazette %s ' % gazette_file
    custom_args += '-serializeTo %s ' % model_file

    cmd = ('java -mx60g -cp ".:%s/*" edu.stanford.nlp.ie.crf.CRFClassifier -prop %s %s' % 
           (corenlp, corenlp_file, custom_args))
    print(cmd)
    corenlp_log = 'corenlp-train.log'
    corenlp_logf = open(corenlp_log, 'w')
    print('Training CoreNLP NER model... ')
    # Note: this will change to run() in Python 3.5
    subprocess.call(cmd, shell=True,
                    stdout=corenlp_logf, stderr=subprocess.STDOUT)
    print(' Saved to %s, logged to %s' % (model_file, corenlp_log))


def main(doc_file, corenlp_file, gazette_file, model_file,
         test=False):

    # Check arguments
    for f in [doc_file, corenlp_file]:
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
    train = True
    if os.path.exists(model_file):
        print('Model file %s exists.' % model_file)
        ans = raw_input(' Do you want to re-train it? [y/n] ')
        if ans not in ['y', 'Y']:
            train = False
    if train:
        train_ner(tsv_file, corenlp_file, gazette_file, model_file)

    # If desired, test the CoreNLP model on the input documents
    if test:
        custom_args = '-loadClassifier %s ' % model_file
        custom_args += '-testFile %s ' % tsv_file

        cmd = ('java -cp ".:%s/*" edu.stanford.nlp.ie.crf.CRFClassifier %s' %
               (corenlp, custom_args))
        print(cmd)
        corenlp_log = 'corenlp-test.log'
        corenlp_logf = open(corenlp_log, 'w')
        print('Testing CoreNLP NER model... ')
        # Note: this will change to run() in Python 3.5
        subprocess.call(cmd, shell=True,
                        stdout=corenlp_logf, stderr=subprocess.STDOUT)
        print(' Logged to %s' % (corenlp_log))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(argument_default=argparse.SUPPRESS, 
                                     description='Train and save NER model.')

    parser.add_argument('doc_file', 
                        help='Text file (.list) with one line per document '
                        'with location of .txt and .ann files')
    parser.add_argument('corenlp_file', 
                        help='Generic CoreNLP properties file (.prop)')
    parser.add_argument('gazette_file',
                        help='Gazette (.gaz.txt) with entity types and names')
    parser.add_argument('model_file', 
                        help='Model file (.ser.gz) to save trained NER model')
    parser.add_argument('-t', '--test', 
                        default=False, action='store_true',
                        help='Test model on input documents')

    args = parser.parse_args()
    main(**vars(args))
