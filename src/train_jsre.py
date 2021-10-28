#!/usr/bin/env python
# This script trains a jSRE model and can optionally evaluate the trained jSRE
# model on the training data.
#
# Copyright notice at bottom of file
#
# Author: Steven Lu
# October 27, 2021

import os
import sys
import glob
import shutil
import subprocess
from shutil import copyfile
import jsre_labeling_corenlp_and_brat


JSRE_TRAIN = 'org.itc.irst.tcc.sre.Train'
JSRE_PREDICT = 'org.itc.irst.tcc.sre.Predict'


def set_jsre_classpath(jsre_root):
    jars = [
        os.path.join(jsre_root, 'dist/xjsre.jar'),
        os.path.join(jsre_root, 'lib/commons-beanutils.jar'),
        os.path.join(jsre_root, 'lib/commons-cli-1.0.jar'),
        os.path.join(jsre_root, 'lib/commons-collections.jar'),
        os.path.join(jsre_root, 'lib/commons-digester.jar'),
        os.path.join(jsre_root, 'lib/commons-logging.jar'),
        os.path.join(jsre_root, 'lib/libsvm-2.8.jar'),
        os.path.join(jsre_root, 'lib/log4j-1.2.8.jar')
    ]

    for jar in jars:
        if not os.path.exists(jar):
            raise RuntimeError('JSRE required JAR file not found: %s' %
                               os.path.abspath(jar))

    os.environ['CLASSPATH'] = ':'.join(jars)


def copy_jsre_config_files(jsre_root):
    src_log_config_file = os.path.join(jsre_root, 'log-config.txt')
    trt_log_config_file = os.path.join(os.getcwd(), 'log-config.txt')
    src_jsre_config_file = os.path.join(jsre_root, 'jsre-config.xml')
    trt_jsre_config_file = os.path.join(os.getcwd(), 'jsre-config.xml')

    if not os.path.exists(src_log_config_file):
        raise RuntimeError('JSRE configuration file log-config.txt not '
                           'found in JSRE root directory %s' %
                           os.path.abspath(jsre_root))

    if not os.path.exists(src_jsre_config_file):
        raise RuntimeError('JSRE configuration file jsre-config.xml not '
                           'found in JSRE root directory %s' %
                           os.path.abspath(jsre_root))

    # Copy the JSRE config files to the current working directory
    copyfile(src_log_config_file, trt_log_config_file)
    copyfile(src_jsre_config_file, trt_jsre_config_file)


def main(in_dir, relation_type, out_dir, kernel, memory_size, n_gram,
         window_size, c, evaluation, jsre_root, jsre_tmp_dir, corenlp_url,
         keep_jsre_examples):
    # Generate jSRE training example files
    jsre_example_dir = os.path.join(jsre_tmp_dir, 'jsre_example_%s' % os.getpid())
    if not os.path.exists(jsre_example_dir):
        os.mkdir(jsre_example_dir)

    jsre_labeling_corenlp_and_brat.main(relation_type, in_dir, jsre_example_dir,
                                        corenlp_url)

    # Concatenate individual jSRE training example files
    jsre_train_file = os.path.join(out_dir, 'jsre-%s.train' % relation_type)
    jsre_train_f = open(jsre_train_file, 'w')
    jsre_example_files = glob.glob('%s/*.examples' % jsre_example_dir)
    print 'Number of jSRE training example files generated: %d' % \
          len(jsre_example_files)
    for jsre_example_file in jsre_example_files:
        with open(jsre_example_file, 'r') as f:
            jsre_train_f.write(f.read())

    jsre_train_f.close()
    if not keep_jsre_examples:
        shutil.rmtree(jsre_example_dir)

    # Set up jSRE environment
    set_jsre_classpath(jsre_root)
    copy_jsre_config_files(jsre_root)

    # Train jSRE model
    out_model_file = os.path.join(out_dir, 'jsre-%s.model' % relation_type)
    train_cmd = ['java', '-mx256M', JSRE_TRAIN, '-m', str(memory_size),
                 '-k', kernel, '-w', str(window_size), '-n', str(n_gram), '-c',
                 str(c), jsre_train_file, out_model_file]
    subprocess.call(train_cmd)

    if not os.path.exists(out_model_file):
        print '[ERROR] Training failed.'
        sys.exit(1)

    # Evaluation
    if evaluation:
        eval_cmd = ['java', JSRE_PREDICT, jsre_train_file, out_model_file,
                    os.path.join(os.getcwd(), 'jsre_predictions.txt')]
        subprocess.call(eval_cmd)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('in_dir', type=str,
                        help='Directory path to documents containing text '
                             '(.txt) and annotations (.ann)')
    parser.add_argument('relation_type', choices=['contains', 'hasproperty'],
                        help='The valid options are contains or has_property')
    parser.add_argument('out_dir', type=str,
                        help='Path to output directory. The trained jSRE model '
                             'and the concatenated jSRE training example file '
                             'will be stored in the output directory.')
    parser.add_argument('-k', '--kernel', choices=['LC', 'GC', 'SL'],
                        default='SL',
                        help='Set type of kernel function. Available options '
                             'are LC (Local Context Kernel), GC (Global Context'
                             ' Kernel), and SL (Shallow Linguistic Context '
                             'Kernel). The default is SL.')
    parser.add_argument('-m', '--memory_size', type=int, default=128,
                        help='Set cache memory size in MB. The default is '
                             '128MB.')
    parser.add_argument('-n', '--n_gram', type=int, default=3,
                        help='set the parameter n-gram of kernels SL and GC. '
                             'The default is 3.')
    parser.add_argument('-w', '--window_size', type=int, default=2,
                        help='set the window size of kernel LC. The default is '
                             '2.')
    parser.add_argument('-c', type=int, default=1,
                        help='set the trade-off between training error and '
                             'margin. The default is 1.')
    parser.add_argument('-e', '--evaluation', action='store_true',
                        help='If this option is enabled, the trained jSRE model'
                             ' will be evaluated with the examples in the '
                             'input file, and the predictions will be stored '
                             'in a text file in the current working directory.'
                             'This option is disabled by default.')
    parser.add_argument('-jr', '--jsre_root', type=str,
                        default='/proj/mte/jSRE/jsre-1.1/',
                        help='Path to jSRE installation directory. Default is '
                             '/proj/mte/jSRE/jsre-1.1/')
    parser.add_argument('-jt', '--jsre_tmp_dir', default='/tmp',
                        help='Path to a directory for jSRE to temporarily '
                             'store input and output files. Default is /tmp')
    parser.add_argument('--corenlp_url', default='http://localhost:9000',
                        help='URL of Stanford CoreNLP server. The default is '
                             'http://localhost:9000')
    parser.add_argument('--keep_jsre_examples', action='store_true',
                        help='If this option is enabled, the jSRE example '
                             'files generated in jsre_tmp_dir will not be '
                             'deleted. This option is by default disabled.')

    args = parser.parse_args()
    main(**vars(args))


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
