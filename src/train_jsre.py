#!/usr/bin/env python
#
# Steven Lu
# October 21, 2021

import os
import sys
import subprocess
from shutil import copyfile


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


def main(in_train_file, out_model_file, kernel, memory_size, n_gram,
         window_size, c, evaluation, jsre_root):
    # Check inputs
    if not os.path.exists(in_train_file):
        print '[ERROR] Input training file not found: %s' % \
              os.path.abspath(in_train_file)
        sys.exit(1)

    # Set up jSRE environment
    set_jsre_classpath(jsre_root)
    copy_jsre_config_files(jsre_root)

    # Train jSRE model
    train_cmd = ['java', '-mx256M', JSRE_TRAIN, '-m', str(memory_size),
                 '-k', kernel, '-w', str(window_size), '-n', str(n_gram), '-c',
                 str(c), in_train_file, out_model_file]
    subprocess.call(train_cmd)

    if not os.path.exists(out_model_file):
        print '[ERROR] Training failed.'
        sys.exit(1)

    # Evaluation
    if evaluation:
        eval_cmd = ['java', JSRE_PREDICT, in_train_file, out_model_file,
                    os.path.join(os.getcwd(), 'jsre_predictions.txt')]
        subprocess.call(eval_cmd)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('in_train_file', type=str,
                        help='Path to the jSRE input file')
    parser.add_argument('out_model_file', type=str, help='jSRE output model')
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

    args = parser.parse_args()
    main(**vars(args))
