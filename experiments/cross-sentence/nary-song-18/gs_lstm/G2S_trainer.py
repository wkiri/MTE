# -*- coding: utf-8 -*-
from __future__ import print_function
import argparse
import os
import sys
import time
import numpy as np
import codecs
import json
import random

from vocab_utils import Vocab
import namespace_utils
import G2S_data_stream
from G2S_model_graph import ModelGraph

FLAGS = None
import tensorflow as tf
tf.logging.set_verbosity(tf.logging.ERROR) # DEBUG, INFO, WARN, ERROR, and FATAL

from nltk.translate.bleu_score import SmoothingFunction, corpus_bleu, sentence_bleu
cc = SmoothingFunction()

import metric_utils

import platform
def get_machine_name():
    return platform.node()

def vec2string(val):
    result = ""
    for v in val:
        result += " {}".format(v)
    return result.strip()


def softmax(x):
    """Compute softmax values for each sets of scores in x."""
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum()


def document_bleu(vocab, gen, ref, suffix=''):
    genlex = [vocab.getLexical(x)[1] for x in gen]
    reflex = [[vocab.getLexical(x)[1],] for x in ref]
    genlst = [x.split() for x in genlex]
    reflst = [[x[0].split()] for x in reflex]
    f = codecs.open('gen.txt'+suffix,'w','utf-8')
    for line in genlex:
        print(line, end='\n', file=f)
    f.close()
    f = codecs.open('ref.txt'+suffix,'w','utf-8')
    for line in reflex:
        print(line[0], end='\n', file=f)
    f.close()
    return corpus_bleu(reflst, genlst, smoothing_function=cc.method3)


def evaluate(sess, valid_graph, devDataStream, options=None, suffix=''):
    devDataStream.reset()
    instances = []
    outputs = []
    dev_loss = 0.0
    dev_right = 0.0
    dev_total = 0.0
    for batch_index in xrange(devDataStream.get_num_batch()): # for each batch
        cur_batch = devDataStream.get_batch(batch_index)
        accu_value, loss_value, output_value = valid_graph.execute(sess, cur_batch, options, is_train=False)
        instances += cur_batch.instances
        outputs += output_value.flatten().tolist()
        dev_loss += loss_value
        dev_right += accu_value
        dev_total += cur_batch.batch_size

    return {'dev_loss':dev_loss, 'dev_accu':1.0*dev_right/dev_total, 'dev_right':dev_right, 'dev_total':dev_total, 'data':(instances,outputs)}


def main(_):
    print('Configurations:')
    print(FLAGS)

    log_dir = FLAGS.model_dir
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    path_prefix = log_dir + "/G2S.{}".format(FLAGS.suffix)
    log_file_path = path_prefix + ".log"
    print('Log file path: {}'.format(log_file_path))
    log_file = open(log_file_path, 'wt')
    log_file.write("{}\n".format(FLAGS))
    log_file.flush()

    # save configuration
    namespace_utils.save_namespace(FLAGS, path_prefix + ".config.json")

    print('Loading train set.')
    if FLAGS.infile_format == 'fof':
        trainset, trn_node, trn_in_neigh, trn_out_neigh, trn_sent = G2S_data_stream.read_nary_from_fof(FLAGS.train_path, FLAGS)
    else:
        trainset, trn_node, trn_in_neigh, trn_out_neigh, trn_sent = G2S_data_stream.read_nary_file(FLAGS.train_path, FLAGS)

    random.shuffle(trainset)
    devset = trainset[:200]
    trainset = trainset[200:]

    print('Number of training samples: {}'.format(len(trainset)))
    print('Number of dev samples: {}'.format(len(devset)))

    max_node = trn_node
    max_in_neigh = trn_in_neigh
    max_out_neigh = trn_out_neigh
    max_sent = trn_sent
    print('Max node number: {}, while max allowed is {}'.format(max_node, FLAGS.max_node_num))
    print('Max parent number: {}, truncated to {}'.format(max_in_neigh, FLAGS.max_in_neigh_num))
    print('Max children number: {}, truncated to {}'.format(max_out_neigh, FLAGS.max_out_neigh_num))
    print('Max entity size: {}, truncated to {}'.format(max_sent, FLAGS.max_entity_size))

    word_vocab = None
    char_vocab = None
    edgelabel_vocab = None
    has_pretrained_model = False
    best_path = path_prefix + ".best.model"
    if os.path.exists(best_path + ".index"):
        has_pretrained_model = True
        print('!!Existing pretrained model. Loading vocabs.')
        word_vocab = Vocab(FLAGS.word_vec_path, fileformat='txt2')
        print('word_vocab: {}'.format(word_vocab.word_vecs.shape))
        char_vocab = None
        if FLAGS.with_char:
            char_vocab = Vocab(path_prefix + ".char_vocab", fileformat='txt2')
            print('char_vocab: {}'.format(char_vocab.word_vecs.shape))
        edgelabel_vocab = Vocab(path_prefix + ".edgelabel_vocab", fileformat='txt2')
    else:
        print('Collecting vocabs.')
        (allWords, allChars, allEdgelabels) = G2S_data_stream.collect_vocabs(trainset)
        print('Number of words: {}'.format(len(allWords)))
        print('Number of allChars: {}'.format(len(allChars)))
        print('Number of allEdgelabels: {}'.format(len(allEdgelabels)))

        word_vocab = Vocab(FLAGS.word_vec_path, fileformat='txt2')
        char_vocab = None
        if FLAGS.with_char:
            char_vocab = Vocab(voc=allChars, dim=FLAGS.char_dim, fileformat='build')
            char_vocab.dump_to_txt2(path_prefix + ".char_vocab")
        edgelabel_vocab = Vocab(voc=allEdgelabels, dim=FLAGS.edgelabel_dim, fileformat='build')
        edgelabel_vocab.dump_to_txt2(path_prefix + ".edgelabel_vocab")

    print('word vocab size {}'.format(word_vocab.vocab_size))
    sys.stdout.flush()

    print('Build DataStream ... ')
    trainDataStream = G2S_data_stream.G2SDataStream(trainset, word_vocab, char_vocab, edgelabel_vocab, options=FLAGS,
                 isShuffle=True, isLoop=True, isSort=False)

    devDataStream = G2S_data_stream.G2SDataStream(devset, word_vocab, char_vocab, edgelabel_vocab, options=FLAGS,
                 isShuffle=False, isLoop=False, isSort=False)
    print('Number of instances in trainDataStream: {}'.format(trainDataStream.get_num_instance()))
    print('Number of instances in devDataStream: {}'.format(devDataStream.get_num_instance()))
    print('Number of batches in trainDataStream: {}'.format(trainDataStream.get_num_batch()))
    print('Number of batches in devDataStream: {}'.format(devDataStream.get_num_batch()))
    sys.stdout.flush()

    # initialize the best bleu and accu scores for current training session
    best_accu = FLAGS.best_accu if FLAGS.__dict__.has_key('best_accu') else 0.0
    if best_accu > 0.0:
        print('With initial dev accuracy {}'.format(best_accu))

    init_scale = 0.01
    with tf.Graph().as_default():
        initializer = tf.random_uniform_initializer(-init_scale, init_scale)
        with tf.name_scope("Train"):
            with tf.variable_scope("Model", reuse=None, initializer=initializer):
                train_graph = ModelGraph(word_vocab=word_vocab, Edgelabel_vocab=edgelabel_vocab,
                                         char_vocab=char_vocab, options=FLAGS, mode='train')

        with tf.name_scope("Valid"):
            with tf.variable_scope("Model", reuse=True, initializer=initializer):
                valid_graph = ModelGraph(word_vocab=word_vocab, Edgelabel_vocab=edgelabel_vocab,
                                         char_vocab=char_vocab, options=FLAGS, mode='evaluate')

        initializer = tf.global_variables_initializer()

        vars_ = {}
        for var in tf.all_variables():
            if "word_embedding" in var.name: continue
            if not var.name.startswith("Model"): continue
            vars_[var.name.split(":")[0]] = var
        saver = tf.train.Saver(vars_)

        sess = tf.Session()
        sess.run(initializer)
        if has_pretrained_model:
            print("Restoring model from " + best_path)
            saver.restore(sess, best_path)
            print("DONE!")

            if abs(best_accu) < 0.00001:
                print("Getting ACCU score for the model")
                best_accu = evaluate(sess, valid_graph, devDataStream, options=FLAGS)['dev_accu']
                FLAGS.best_accu = best_accu
                namespace_utils.save_namespace(FLAGS, path_prefix + ".config.json")
                print('ACCU = %.4f' % best_accu)
                log_file.write('ACCU = %.4f\n' % best_accu)

        print('Start the training loop.')
        train_size = trainDataStream.get_num_batch()
        max_steps = train_size * FLAGS.max_epochs
        last_step = 0
        total_loss = 0.0
        start_time = time.time()
        for step in xrange(max_steps):
            cur_batch = trainDataStream.nextBatch()
            _, loss_value, _ = train_graph.execute(sess, cur_batch, FLAGS, is_train=True)
            total_loss += loss_value

            if step % 100==0:
                print('{} '.format(step), end="")
                sys.stdout.flush()

            # Save a checkpoint and evaluate the model periodically.
            if (step + 1) % trainDataStream.get_num_batch() == 0 or (step + 1) == max_steps:
                print()
                duration = time.time() - start_time
                print('Step %d: loss = %.2f (%.3f sec)' % (step, total_loss/(step-last_step), duration))
                log_file.write('Step %d: loss = %.2f (%.3f sec)\n' % (step, total_loss/(step-last_step), duration))
                sys.stdout.flush()
                log_file.flush()
                last_step = step
                total_loss = 0.0

                # Evaluate against the validation set.
                start_time = time.time()
                print('Validation Data Eval:')
                res_dict = evaluate(sess, valid_graph, devDataStream, options=FLAGS, suffix=str(step))
                dev_loss = res_dict['dev_loss']
                dev_accu = res_dict['dev_accu']
                dev_right = int(res_dict['dev_right'])
                dev_total = int(res_dict['dev_total'])
                print('Dev loss = %.4f' % dev_loss)
                log_file.write('Dev loss = %.4f\n' % dev_loss)
                print('Dev accu = %.4f %d/%d' % (dev_accu, dev_right, dev_total))
                log_file.write('Dev accu = %.4f %d/%d\n' % (dev_accu, dev_right, dev_total))
                log_file.flush()
                if best_accu < dev_accu:
                    print('Saving weights, ACCU {} (prev_best) < {} (cur)'.format(best_accu, dev_accu))
                    saver.save(sess, best_path)
                    best_accu = dev_accu
                    FLAGS.best_accu = dev_accu
                    namespace_utils.save_namespace(FLAGS, path_prefix + ".config.json")
                    json.dump(res_dict['data'], open(FLAGS.output_path,'w'))
                duration = time.time() - start_time
                print('Duration %.3f sec' % (duration))
                sys.stdout.flush()

                log_file.write('Duration %.3f sec\n' % (duration))
                log_file.flush()

    log_file.close()

def enrich_options(options):
    if not options.__dict__.has_key("infile_format"):
        options.__dict__["infile_format"] = "fof"

    return options


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config_path', type=str, help='Configuration file.')

    #os.environ["CUDA_DEVICE_ORDER"]="PCI_BUS_ID"   # see issue #152
    #os.environ["CUDA_VISIBLE_DEVICES"]="2"

    print("CUDA_VISIBLE_DEVICES " + os.environ['CUDA_VISIBLE_DEVICES'])
    FLAGS, unparsed = parser.parse_known_args()


    if FLAGS.config_path is not None:
        print('Loading the configuration from ' + FLAGS.config_path)
        FLAGS = namespace_utils.load_namespace(FLAGS.config_path)

    FLAGS = enrich_options(FLAGS)

    sys.stdout.flush()
    tf.app.run(main=main, argv=[sys.argv[0]] + unparsed)
