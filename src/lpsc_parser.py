from __future__ import print_function

import os
import re
import sys
import json
from tqdm import tqdm
from log_utils import LogUtil
from io_utils import read_lines
from paper_parser import PaperParser
from ads_parser import AdsParser
from jsre_parser import JsreParser
from unary_parser import UnaryParser


class LpscParser(PaperParser):
    """ The LpscParser removes special text content/format (e.g., LPSC
    conference header) from the two-page abstracts published at Lunar and
    Planetary Science Conference
    """
    PDF_TYPE = "application/pdf"

    def __init__(self, parser_name='lpsc_parser'):
        super(LpscParser, self).__init__(parser_name)

    @staticmethod
    def extract_references(content):
        references = {}
        content = content.replace("\n", "\\n")
        matches = re.findall(
            '(\[[0-9]+\][^\[]*?(?=\[|Acknowledge|Fig|Table|Conclusion|pdf))',
            content)
        if matches:
            for match in matches:
                ref_id = LpscParser.get_reference_id(match)
                # No reference id exist -- skip it
                if ref_id != -1:
                    value = match.replace('\\n', '\n')
                    references[ref_id] = value
        return references

    @staticmethod
    def get_reference_id(reference):
        ref_id = -1
        match = re.search('\[[0-9]+\]', reference)
        if match:
            ref_id = int(match.group(0).strip('[]'))
        return ref_id

    def parse(self, text, metadata):
        paper_dict = super(LpscParser, self).parse(text, metadata)
        cleaned_text = paper_dict['cleaned_content']

        # Remove xxxx.PDF
        cleaned_text = re.sub(r'([0-9][0-9][0-9][0-9].PDF)', '', cleaned_text,
                              flags=re.IGNORECASE)
        # And "xx(th|st) Lunar and Planetary Science Conference ((19|20)xx)"
        cleaned_text = re.sub(r'([0-9][0-9].. Lunar and Planetary Science '
                              r'Conference \((19|20)[0-9][0-9]\)) ?', '',
                              cleaned_text, flags=re.IGNORECASE)
        # And "Lunar and Planetary Science XXXIII (2002)"
        # with Roman numeral and optional year
        cleaned_text = re.sub(r'(Lunar and Planetary Science '
                              r'[CDILVXM]+ (\((19|20)[0-9][0-9]\))?) ?', '',
                              cleaned_text, flags=re.IGNORECASE)

        # Extract references
        refs = self.extract_references(text)

        return {
            'references': refs.values(),
            'cleaned_content': cleaned_text
        }


def process(in_file, in_list, out_file, log_file, tika_server_url,
            corenlp_server_url, ner_model, gazette_file, relation_types,
            jsre_root, jsre_models, jsre_tmp_dir, containee_model_file,
            container_model_file, entity_linking_method, gpu_id, batch_size,
            ads_url, ads_token):
    # Log input parameters
    logger = LogUtil(log_file)
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
        logger.info('[ERROR] in_file and in_list cannot be provided '
                    'simultaneously')
        sys.exit(1)

    if len(relation_types) != len(jsre_models):
        print('[ERROR] There should be a one-to-one mapping for relation types '
              'and jSRE models.')
        sys.exit(1)

    ads_parser = AdsParser(ads_token, ads_url, tika_server_url)
    lpsc_parser = LpscParser()

    # Note: this is temporary solution as it requires users to carefully provide
    # inputs to the script. A better solution would be restrict users to provide
    # inputs that are mutual exclusive (e.g., if jsre_model is provided, then
    # unary parser's options should be disallowed).
    # Steven Lu, September 2, 2021
    jsre_parser = None
    unary_parser = None
    if jsre_models:
        logger.info('relation_types: %s' % json.dumps(relation_types))
        logger.info('jsre_root: %s' % os.path.abspath(jsre_root))
        logger.info('jsre_models: %s' % json.dumps(jsre_models))
        logger.info('jsre_tmp_dir: %s' % os.path.abspath(jsre_tmp_dir))

        jsre_parser = JsreParser(corenlp_server_url, ner_model, gazette_file,
                                 relation_types, jsre_root, jsre_models,
                                 jsre_tmp_dir)
    elif container_model_file and containee_model_file and entity_linking_method:
        logger.info('container_model_file: %s' %
                    os.path.abspath(container_model_file))
        logger.info('containee_model_file: %s' %
                    os.path.abspath(containee_model_file))
        logger.info('entity_linking_method: %s' % entity_linking_method)
        logger.info('gpu_id: %s' % str(gpu_id))

        unary_parser = UnaryParser(corenlp_server_url, ner_model, gazette_file,
                                   containee_model_file, container_model_file,
                                   gpu_id=gpu_id)

    if in_file:
        files = [in_file]
    else:
        files = read_lines(in_list)

    out_f = open(out_file, 'wb', 1)
    for f in tqdm(files):
        try:
            base_name = os.path.basename(f)
            logger.info('Processing %s' % base_name)
            base_name = base_name.split('.')[0]
            year, abs_num = base_name.split('_')
            query_dict = {'lpsc_query_strategy': {
                'year': year,
                'abstract_number': abs_num
            }}

            ads_dict = ads_parser.parse(f, query_dict)
            lpsc_dict = lpsc_parser.parse(ads_dict['content'],
                                          ads_dict['metadata'])

            if jsre_parser is not None:
                rel_dict = jsre_parser.parse(lpsc_dict['cleaned_content'])
            else:
                rel_dict = unary_parser.parse(
                    lpsc_dict['cleaned_content'], batch_size=batch_size,
                    entity_linking_method=entity_linking_method)

            ads_dict['content_ann_s'] = lpsc_dict['cleaned_content']
            ads_dict['references'] = lpsc_dict['references']
            ads_dict['metadata']['ner'] = rel_dict['ner']
            ads_dict['metadata']['rel'] = rel_dict['relation']
            ads_dict['metadata']['sentences'] = rel_dict['sentences']
            ads_dict['metadata']['X-Parsed-By'] = rel_dict['X-Parsed-By']

            out_f.write(json.dumps(ads_dict))
            out_f.write('\n')
        except Exception as e:
            logger.info('LPSC parser failed: %s' % os.path.abspath(f))
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
    parser.add_argument('-l', '--log_file', default='./lpsc-parser-log.txt',
                        help='Log file that contains processing information. '
                             'It is default to ./lpsc-parser-log.txt unless '
                             'otherwise specified.')
    parser.add_argument('-p', '--tika_server_url', required=False,
                        help='Tika server URL')
    parser.add_argument('-c', '--corenlp_server_url',
                        default='http://localhost:9000',
                        help='CoreNLP Server URL')
    parser.add_argument('-n', '--ner_model', required=False,
                        help='Path to a Named Entity Recognition (NER) model')
    parser.add_argument('-g', '--gazette_file', required=False,
                        help='Path to a gazette file that consists of '
                             '"Entity_type Entity_name" pairs')
    parser.add_argument('-rt', '--relation_types', nargs='+', required=True,
                        choices=['Contains', 'HasProperty'],
                        help='Relation types. Options are Contains and '
                             'HasProperty.')
    parser.add_argument('-jr', '--jsre_root', default='/proj/mte/jSRE/jsre-1.1',
                        help='Path to jSRE installation directory. Default is '
                             '/proj/mte/jSRE/jsre-1.1')
    parser.add_argument('-jm', '--jsre_models', nargs='+', required=True,
                        help='Path to jSRE model')
    parser.add_argument('-jt', '--jsre_tmp_dir', default='/tmp',
                        help='Path to a directory for jSRE to temporarily '
                             'store input and output files. Default is /tmp')
    parser.add_argument('-cnte', '--containee_model_file', required=False,
                        help='Path to a trained Containee model')
    parser.add_argument('-cntr', '--container_model_file', required=False,
                        help='Path to a trained Container model')
    parser.add_argument('-m', '--entity_linking_method', required=False,
        choices=['closest_container_closest_containee',
                 'closest_target_closest_component', 'closest_containee',
                 'closest_container', 'closest_component',  'closest_target'],
        help='Method to form relations between entities. '
             '[closest_containee]: for each Container instance, link it to its '
             'closest Containee instance with a Contains relation, '
             '[closest_container]: for each Containee instance, link it to its '
             'closest Container instance with a Contains relation, '
             '[closest_component]: for each Container instance, link it to its '
             'closest Component instance with a Contains relation, '
             '[closest_target]: for each Containee instance, link it to its '
             'closest Target instance with a Contains relation, '
             '[closest_target_closest_component]: union the relation instances '
             'found by closest_target and closest_component, '
             '[closest_container_closest_containee]: union the relation '
             'instances found by closest_containee and closest_container. '
             'This is the best method on the MTE test set')
    parser.add_argument('-gid', '--gpu_id', default=-1, type=int,
                        help='GPU ID. If set to negative then no GPU would be used.')
    parser.add_argument('-b', '--batch_size',
                        default=10,
                        type=int,
                        help='Batch size at inference time.')
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
