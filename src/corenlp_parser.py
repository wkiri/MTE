from __future__ import print_function

import os
import re
import sys
import json
import string
import urllib
import itertools
from tqdm import tqdm
from log_utils import LogUtil
from parser import Parser
from io_utils import read_lines
from ads_parser import AdsParser
from pycorenlp import StanfordCoreNLP

# The following two lines make CoreNLP happy
reload(sys)
sys.setdefaultencoding('UTF8')


class CoreNLPParser(Parser):
    """ The CoreNLPParser class builds upon Stanford CoreNLP package """

    CORENLP_PARSER = "edu.stanford.nlp.pipeline.CoreNLPServer"
    mypunc = string.punctuation
    for p in ['_', '\+', '-', '\.']:
        mypunc = re.sub(p, '', mypunc)

    def __init__(self, corenlp_server_url, ner_model, gazette_file,
                 parser_name='corenlp_parser'):
        super(CoreNLPParser, self).__init__(parser_name)

        self.corenlp = StanfordCoreNLP(corenlp_server_url)
        self.props = {
            'annotators': 'tokenize,ssplit,lemma,pos,ner',
            'outputFormat': 'json',
            # dont want SUTime model
            'ner.useSUTime': False,
            # Dont want numeric classifier
            'ner.applyNumericClassifiers': False,
            'timeout': '60000',
            # Don't need fine grained recognition with corenlp built-in NER
            # models
            'ner.applyFineGrained': False
        }
        if ner_model:
            if not os.path.exists(ner_model):
                raise RuntimeError('NER model not found: %s' %
                                   os.path.abspath(ner_model))
            self.props['ner.model'] = ner_model

        self.gazette_targets = None
        if gazette_file:
            if os.path.exists(gazette_file):
                self.gazette_targets = self.read_gazette(gazette_file)
            else:
                raise RuntimeError('Gazette file provided (%s) does not exist.'
                                   % os.path.abspath(gazette_file))

    @staticmethod
    def read_gazette(gazette_file):
        with open(gazette_file, 'r') as f:
            lines = f.readlines()
            targets = [l.strip()[7:] for l in lines if 'Target' in l]

            # Add a version with space converted to _
            targets += [re.sub(' ', '_', cc) for cc in targets if ' ' in cc]
            # Chemcam-specific processing:
            # Add a version with trailing _CCAM or _ccam removed
            targets += [cc[:-5] for cc in targets
                        if cc.endswith('_CCAM') or cc.endswith('_ccam')]
            # Add a version with trailing _DRT or _drt removed
            targets += [cc[:-4] for cc in targets
                        if cc.endswith('_DRT') or cc.endswith('_drt')]
            # Add a version with trailing _RMI or _rmi removed
            targets += [cc[:-4] for cc in targets
                        if cc.endswith('_RMI') or cc.endswith('_rmi')]
            # Add a version with trailing _1 or _2 removed
            targets += [cc[:-2] for cc in targets
                        if cc.endswith('_1') or cc.endswith('_2')]
            # Add a version with _ converted to space
            targets += [re.sub('_', ' ', cc) for cc in targets
                        if '_' in cc]

        # Get rid of duplicates
        targets = list(set(targets))

        return targets

    @staticmethod
    def gazette_target_match(text, gazette_targets):
        # Master list of all match targets
        targets = list()

        # Initialize counters
        span_start = 0

        # Specifying ' ' explicitly means that all single spaces
        # will cause a split.  This way we can update span_start
        # correctly even if there are multiple spaces present.
        words = text.split(' ')
        for (i, w) in enumerate(words):
            # This check slows us down, but ensures we didn't mess up the
            # indexing!
            if w != text[span_start: span_start + len(w)]:
                raise RuntimeError('<%s> and <%s> do not match.' %
                                   (w, text[span_start:span_start+len(w)]))

            # Remove any trailing \n etc.
            w_strip = w.strip()

            # Remove any punctuation, except '_' and '+' (ions) and '-'
            # and '.' (e.g., Mt. Sharp)
            w_strip = re.sub('[%s]' % re.escape(CoreNLPParser.mypunc), '',
                             w_strip)

            # Try the word and also the two-word and three-word phrases it's in
            phrases = [(w, w_strip)]
            if i < len(words) - 1:
                w_next_1 = re.sub('[%s]' % re.escape(CoreNLPParser.mypunc), '',
                                  words[i + 1])
                phrases += [(' '.join([w, words[i + 1]]),
                             ' '.join([w_strip, w_next_1]))]
            if i < len(words) - 2:
                w_next_2 = re.sub('[%s]' % re.escape(CoreNLPParser.mypunc), '',
                                  words[i + 2])
                phrases += [(' '.join([w, words[i + 1], words[i + 2]]),
                             ' '.join([w_strip, w_next_1, w_next_2]))]

            for (my_word, my_word_strip) in phrases:
                # Characters we stripped off but still need to count in spans
                extra = 0

                # If it ends with - or ., take it off
                if (my_word_strip.endswith('-') or
                        my_word_strip.endswith('.')):
                    my_word_strip = my_word_strip[:-1]
                    extra += 1

                if my_word_strip not in gazette_targets:
                    span_end = span_start + len(my_word_strip) + extra
                else:
                    # This handles leading and trailing punctuation,
                    # but not cases where there is internal punctuation
                    try:
                        span_start_strip = span_start + \
                                           my_word.index(my_word_strip)
                    except: # internal punctuation, so skip it
                        # (fine as long as ONE of these succeeds...
                        # otherwise span_start needs an update)
                        continue

                    span_end = span_start_strip + len(my_word_strip)

                    if text[span_start_strip:span_end] != my_word_strip:
                        raise RuntimeError('<%s> and <%s> do not match.' %
                                           (my_word_strip,
                                            text[span_start_strip: span_end]))

                    targets.append({
                        'label': 'Target',
                        'begin': span_start_strip,
                        'end': span_end,
                        'text': my_word_strip,
                        'source': 'gazette'
                    })

            # Either way, update span_start
            span_end = span_start + len(w)

            # Assumes followed by space
            span_start = span_end + 1

        return targets

    def parse(self, text):
        """ Named entity recognition (NER) using stanford CoreNLP package

        Args:
            text (str): A string (can be a long string) in which Named Entity
                Recognition will run.
        Return:
            this function returns a dictionary contains the NERs identified,
            sentences extracted, and name of the source parser
        """
        if type(text) != str:
            corenlp_text = text.encode('utf8')
        if corenlp_text[0].isspace():  # dont strip white spaces
            corenlp_text = '.' + corenlp_text[1:]

        # Quote (with percent-encoding) reserved characters in URL for CoreNLP
        corenlp_text = urllib.quote(corenlp_text)
        output = self.corenlp.annotate(corenlp_text, properties=self.props)

        # flatten sentences and tokens
        tokenlists = [s['tokens'] for s in output['sentences']]
        tokens = itertools.chain.from_iterable(tokenlists)
        names = []
        for token in tokens:
            if token['ner'] != 'O':
                name = {
                    'label': token['ner'],
                    'begin': token['characterOffsetBegin'],
                    'end': token['characterOffsetEnd'],
                    'text': token['originalText'],
                    'source': 'corenlp'
                }
                names.append(name)

        # Handle multi-word tokens:
        # Merge any adjacent Target tokens, if of the same type and
        # separated by a space, into one span.
        names.sort(key=lambda x: int(x['begin']))
        new_names = []
        skip_names = []
        for n in names:
            if n in skip_names:
                continue
            next_name = [n2 for n2 in names if
                         n['label'] == 'Target' and
                         n2['label'] == 'Target' and
                         int(n2['begin']) == int(n['end']) + 1]
            if len(next_name) > 0:
                n['text'] += ' ' + next_name[0]['text']
                n['end'] = next_name[0]['end']
                skip_names.append(next_name[0])

            # Either way, save this one
            new_names.append(n)

        if self.gazette_targets:
            # Get all matching targets
            matching_targets = self.gazette_target_match(text,
                                                         self.gazette_targets)

            # Remove duplicates
            for target_dict in matching_targets:
                for name_dict in new_names:
                    if target_dict['label'] == name_dict['label'] and \
                            target_dict['begin'] == name_dict['begin'] and \
                            target_dict['end'] == name_dict['end'] and \
                            target_dict['text'] == name_dict['text']:
                        matching_targets.remove(target_dict)
                        break

            if len(matching_targets) > 0:
                # Update the token 'ner' fields too
                tokenlists = [s['tokens'] for s in output['sentences']]
                for target_dict in matching_targets:
                    tokens = itertools.chain.from_iterable(tokenlists)
                    # Targets can be multi-word, but we need to annotate tokens.
                    # We will make an assumption that any token in the valid range
                    # with a matching term should be updated.
                    match_tokens = [t for t in tokens 
                                    if (t['characterOffsetBegin'] >= target_dict['begin'] and \
                                        t['characterOffsetEnd'] <= target_dict['end'] and \
                                        t['originalText'] in target_dict['text'])]
                    for t in match_tokens:
                        t['ner'] = target_dict['label']
                        #print('Updated %s to %s' % (t['originalText'], target_dict['label']))

            # Combine NER items and gazette targets
            new_names += matching_targets

        return {
            'ner': new_names,
            'X-Parsed-By': CoreNLPParser.CORENLP_PARSER,
            'sentences': output['sentences']
        }


def process(in_file, in_list, out_file, log_file, tika_server_url,
            corenlp_server_url, ner_model, gazette_file, ads_url, ads_token):
    # Log input parameters
    logger = LogUtil('corenlp-parser', log_file)
    logger.info('Input parameters')
    logger.info('in_file: %s' % in_file)
    logger.info('in_list: %s' % in_list)
    logger.info('out_file: %s' % out_file)
    logger.info('tika_server_url: %s' % tika_server_url)
    logger.info('corenlp_server_url: %s' % corenlp_server_url)
    logger.info('ner_model: %s' % os.path.abspath(ner_model))
    logger.info('gazette_file: %s' % gazette_file)
    logger.info('ads_url: %s' % ads_url)
    logger.info('ads_token: %s' % ads_token)

    if in_file and in_list:
        print('[ERROR] in_file and in_list cannot be provided simultaneously')
        sys.exit(1)

    ads_parser = AdsParser(ads_token, ads_url, tika_server_url)
    corenlp_parser = CoreNLPParser(corenlp_server_url, ner_model, gazette_file)

    if in_file:
        files = [in_file]
    else:
        files = read_lines(in_list)

    out_f = open(out_file, 'wb', 1)
    for f in tqdm(files):
        try:
            ads_dict = ads_parser.parse(f)
            corenlp_dict = corenlp_parser.parse(ads_dict['content'])

            ads_dict['metadata']['ner'] = corenlp_dict['ner']
            ads_dict['metadata']['X-Parsed-By'].append(corenlp_dict['X-Parsed-By'])
            ads_dict['metadata']['sentences'] = corenlp_dict['sentences']

            out_f.write(json.dumps(ads_dict))
            out_f.write('\n')
        except Exception as e:
            logger.info('CoreNLP parser failed: %s' % os.path.abspath(f))
            logger.error(e)

    out_f.close()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    input_parser = parser.add_mutually_exclusive_group(required=True)

    input_parser.add_argument('-i', '--in_file', help='Path to input file')
    input_parser.add_argument('-li', '--in_list', help='Path to input list')
    parser.add_argument('-o', '--out_file', required=True,
                        help='Path to output JSON file')
    parser.add_argument('-l', '--log_file', default='./corenlp-parser-log.txt',
                        help='Log file that contains processing information. '
                             'It is default to ./corenlp-parser-log.txt unless '
                             'otherwise specified.')
    parser.add_argument('-p', '--tika_server_url', required=False,
                        help='Tika server URL')
    parser.add_argument('-c', '--corenlp_server_url',
                        default='http://localhost:9000',
                        help='CoreNLP Server URL')
    parser.add_argument('-n', '--ner_model', required=False,
                        help='Path to a Named Entity Recognition (NER) model ')
    parser.add_argument('-g', '--gazette_file', required=False,
                        help='Path to a gazette file that consists of '
                             '"Entity_type Entity_name" pairs')
    parser.add_argument('-a', '--ads_url',
                        default='https://api.adsabs.harvard.edu/v1/search/query',
                        help='ADS RESTful API. The ADS RESTful API should not '
                             'need to be changed frequently unless someting at '
                             'the ADS is changed.')
    parser.add_argument('-t', '--ads_token',
                        default='jON4eu4X43ENUI5ugKYc6GZtoywF376KkKXWzV8U',
                        help='The ADS token, which is required to use the ADS '
                             'RESTful API. The token was obtained using the '
                             'instructions at '
                             'https://github.com/adsabs/adsabs-dev-api#access. '
                             'The ADS token should not need to be changed '
                             'frequently unless something at the ADS is '
                             'changed.')

    args = parser.parse_args()
    process(**vars(args))
