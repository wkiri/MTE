import sys, os, json, torch, logging, numpy as np, argparse

from tqdm import tqdm
from copy import deepcopy 
from extraction_utils import extract_system_entities
from model import Model
from instance import Span_Instance
from model_utils import to_device, get_closest_container_and_containee, get_closest_target_and_component, get_closest_container, get_closest_containee, get_closest_target, get_closest_component
from dataset import MyDataset, collate 
from config import label2ind, ind2label
from torch.utils.data import DataLoader
#@Steven: Please set up the paths such that they could be imported
from ioutils import read_lines
from ads_parser import AdsParser
from corenlp_parser import CoreNLPParser 

logging.basicConfig(level = logging.INFO) # @Steven: please use your logger here 


class UnaryParser(CoreNLPParser):
    """ Relation extraction using unary classifiers. The unaryParser class depends on
    the outputs provided by the CoreNLPParser class.
    """

    def __init__(self, corenlp_server_url, ner_model_file, containee_model_file, container_model_file, gpu_id = 0 ):
        """
        Args:
            containee_model_file: 
                pretrained model file (.ckpt) for Containee 
            
            container_model_file:
                pretrained model file (.ckpt) for Container  
            
            gpu_id:
                id of GPU. Negative gpu_id means no GPU to be used. 
        """
       # super(UnaryParser, self).__init__(corenlp_server_url,ner_model_file,'jsre_parser')

        self.corenlp_server_url = corenlp_server_url
        self.ner_model_file = ner_model_file
        self.containee_model_file = containee_model_file
        self.container_model_file = container_model_file
        self.containee = None 
        self.container = None 
        self.gpu_id = gpu_id


        logging.info('Loading pretrained Containee')
        self.containee =  to_device(self.load_unary_model('Containee'), self.gpu_id)
        self.containee.eval()


        logging.info('Loading pretrained Container')
        self.container = to_device(self.load_unary_model('Container'), self.gpu_id)
        self.container.eval()


    def load_unary_model(self, model_name):
        """ Load pretrained Container and Containee model"""
        
        model = Model(model_name, gpu_id = self.gpu_id)
        if model_name == 'Container':
            model.load_state_dict(torch.load(self.container_model_file))
        else:
            model.load_state_dict(torch.load(self.containee_model_file))

        return model 

    def predict(self, model, dataloader):
        
        pred_instances = []
        soft = torch.nn.Softmax(dim = 1)
        
        with torch.no_grad():
            for i, item in enumerate(dataloader):
                logits =model.forward(item)
                scores = soft(logits).cpu().numpy()
                y_preds = np.argmax(scores,1)

                for ins, y_pred, score in zip(item["instances"], y_preds, scores):
                    if score[0] > 0.5:
                        y_pred = 0
                    else:
                        y_pred = 1
                    ins.pred_relation_label = ind2label[y_pred]
                    ins.pred_score = score
                    pred_instances.append(ins)

        return pred_instances



    # def parse(self, text, corenlp_file = None, batch_size = 10, entity_linking_method = 'closest_container_closest_containee'):
    def parse(self, text, batch_size = 10, entity_linking_method = 'closest_container_closest_containee'):
        
        """
        Args:
            text:   
                text of the document 

            batch_size:
                batch size at prediction time.

            entity_linking_method:
                strategy to form Contains relations from Targets and Components.  
                
                Options:
                    closest_containee:
                        for each Container instance, link it to its closest Containee instance with a Contains relation
                    closest_container:
                        for each Containee instance, link it to its closest Container instance with a Contains relation
                    closest_component:
                        for each Container instance, link it to its closest Component instance with a Contains relation,
                    closest_target:
                        for each Containee instance, link it to its closest Target instance with a Contains relation
                    union_closest_containee_closest_container:
                        union the relation instances found by closest_containee and closest_container
        """

        entity_linking_methods = [
            'closest_container_closest_containee',
            'closest_target_closest_component'
            'closest_containee',
            'closest_container',
            'closest_component',
            'closest_target'
        ]

        if entity_linking_method not in entity_linking_methods:
            logging.error(f"Unrecognized entity linking method: {entity_linking_method}. You need to choose from [{', '.join(entity_linking_methods)}] !")
        
        # # get parsing results from CoreNLP
        # if corenlp_file is not None:
        #     with open(corenlp_file, 'r') as f:
        #         corenlp_dict = json.load(f)
        # else:
        #     corenlp_dict = super(UnaryParser, self).parse(text)
        
        corenlp_dict = super(UnaryParser, self).parse(text)

        # extract entities from the parsing results 
        entities = [e for e in extract_system_entities(doc = corenlp_dict, use_component = True) if e['label'] in ['Target', 'Component']]

        num_target = len([ 1 for e in entities if e['label'] == 'Target'])
        num_component = len([1 for e in entities if e['label'] == 'Component'])

        logging.info(f'Extracted {num_target} Targets and {num_component} Components')

        # map extracted component and target entities to their corresponding sentences
        sentid2entities = {}
        for e in entities:
            sentid = e['sentid']
            if e['label'] not in ['Target', 'Component']:
                continue

            if sentid not in sentid2entities:
                sentid2entities[sentid] = []
            sentid2entities[sentid].append(e)

        # make target and component instances for inference. Here we only make inference for Target/Component that co-occurs with some other Component/Target in the same sentence. If the sentence has only components or targets, we assume that there wouldn't be any within-sentence Contains relations in this sentence. As a result, the entities in this sentence wouldn't be taken as an inference candidate for Container and Containee. 
        target_instances = []
        component_instances = [] 
        exceed_len_cases = 0 
        for sentid, sent_entities in sentid2entities.items():
        
            possible_entity_labels = set([e['label'] for e in sent_entities])   
            if 'Target' not in possible_entity_labels or 'Component' not in possible_entity_labels:
                continue 

            sent_toks = [token['word'] for token in corenlp_dict['sentences'][sentid]['tokens']]

            seen_spanids = set() # used to remove duplicates in case
            for e in sent_entities:
                # e doesn't have any venue, year and docname, since they are not provided in the arguments. So just assign a 'None' to these. 
                span = Span_Instance('None', 'None', 'None', e['doc_start_char'], e['doc_end_char'], e['text'], e['label'], sent_toks = deepcopy(sent_toks), sentid = sentid, sent_start_idx = e['sent_start_idx'], sent_end_idx = e['sent_end_idx'])

                if span.span_id not in seen_spanids:
                    tokenizer = self.containee.tokenizer if e['label'] == 'Component' else self.container.tokenizer 
                    exceed = span.insert_type_markers(tokenizer, max_len = 512) # insert entity markers around the entity in its sentence, convert the sentence to token ids and check if the insertion makes the number of token ids more than 512

                    if e['label'] == 'Target':
                        target_instances.append(span)
                    else:
                        component_instances.append(span)
                    exceed_len_cases += exceed

        logging.info(f'Collected {len(target_instances)} Targets and {len(component_instances)} Components that co-occur with Components/Targets in the same sentence for relation inference.')
        logging.info(f'{exceed_len_cases} of them exceed 512 tokens after inserting entity markers in the sentences.')


        # make dataset the model takes for prediction
        target_dataset = MyDataset(target_instances)
        component_dataset = MyDataset(component_instances)

        target_dataloader = DataLoader(target_dataset, batch_size = batch_size, collate_fn = collate)
        component_dataloader = DataLoader(component_dataset, batch_size= batch_size, collate_fn = collate)

        # Inference using Container and Containee
        target_preds = self.predict(self.container, target_dataloader)
        component_preds = self.predict(self.containee, component_dataloader)

        contains_relations = self.form_relations(target_preds, component_preds, corenlp_dict, entity_linking_method)

        return {
            'ner': corenlp_dict['ner'],
            'sentences': corenlp_dict['sentences'],
            'relation': contains_relations,
            'X-Parsed-By': f'UnaryParser:{entity_linking_method}' #@Steven: I am not sure what this entry wants. Please modify this. 
        }

    def form_relations(self, target_preds, component_preds, corenlp_dict, entity_linking_method):

        method2funct = {
            'closest_component': get_closest_component, 
            'closest_container': get_closest_container,
            'closest_containee': get_closest_containee,
            'closest_target': get_closest_target, 
            'closest_container_closest_containee': get_closest_container_and_containee,
            'closest_target_closest_component': get_closest_target_and_component
        }

        rels = method2funct[entity_linking_method](target_preds, component_preds)

        contains_relations = []
        for target, component in rels: 
            sentid = target.sentid
            contains_relations.append({
                'label': 'contains',
                # std text in the following means canonical texts (texts processed by canonical_target_name or canonical_component_name)
                'target_names': [target.std_text],
                'cont_names': [component.std_text],
                'target_ids': ['%s_%d_%d' % (target.ner_label.lower(),
                                             target.doc_start_char,
                                             target.doc_end_char)],
                'cont_ids': ['%s_%d_%d' % (component.ner_label.lower(),
                                           component.doc_start_char,
                                           component.doc_end_char)],
                'sentence':  ' '.join([t['originalText']
                                       for t in corenlp_dict['sentences'][sentid]['tokens']]),
                'source': f'UnaryParser:{entity_linking_method}' #@Steven: I am not sure what this entry wants. Please modify this. 
            })
        return contains_relations


# if __name__ == "__main__":

#     parser = UnaryParser("", "", '../../contain-experiments/local_classifiers/containee/temp/trained_model.ckpt', '../../contain-experiments/local_classifiers/container/temp/trained_model.ckpt', gpu_id = 0)
#     ret = parser.parse("", corenlp_file = "/uusoc/exports/scratch/yyzhuang/MTE/parse-with-sysners/lpsc15-C-raymond-sol1159-v3-utf8/1249.txt.json", batch_size = 10, entity_linking_method = 'closest_container_closest_containee')
#     for k in ret['relation']:
#         print(k['target_names'], k['cont_names'])


def process(in_file, in_list, out_file, log_file, tika_server_url, ads_url, ads_token, corenlp_server_url, ner_model, containee_model_file, container_model_file, entity_linking_method, gpu_id, batch_size):

    # Log input parameters
    logger = logging.getLogger() # @Stevem: Please change the following logging code with your Logger
    logger.info('Input parameters')
    logger.info('in_file: %s' % in_file)
    logger.info('in_list: %s' % in_list)
    logger.info('out_file: %s' % out_file)
    logger.info('log_file: %s' % log_file)
    logger.info('tika_server_url: %s' % tika_server_url)
    logger.info('ads_url: %s' % ads_url)
    logger.info('ads_token: %s' % ads_token)
    logger.info('corenlp_server_url: %s' % corenlp_server_url)
    logger.info('ner_model: %s' % os.path.abspath(ner_model))
    logger.info('container_model_file: %s' % os.path.abspath(container_model_file))
    logger.info('containee_model_file: %s' % os.path.abspath(containee_model_file))
    logger.info('entity_linking_method: %s' % entity_linking_method)
    logger.info('gpu_id: %s' % str(gpu_id))

    
    if in_file and in_list:
        raise NameError('[ERROR] in_file and in_list cannot be provided simultaneously')

    ads_parser = AdsParser(ads_token, ads_url, tika_server_url)

    unary_parser = UnaryParser(corenlp_server_url, ner_model, containee_model_file, container_model_file, gpu_id = gpu_id)

    if in_file:
        files = [in_file]
    else:
        files = read_lines(in_list)

    out_f = open(out_file, 'wb', 1)
    for f in tqdm(files):
        try:
            ads_dict = ads_parser.parse(f)

            unary_dict = unary_parser.parse(ads_dict['content'], batch_size = batch_size, entity_linking_method = entity_linking_method)

            ads_dict['metadata']['ner'] = unary_dict['ner']
            ads_dict['metadata']['rel'] = unary_dict['relation']
            ads_dict['metadata']['sentences'] = unary_dict['sentences']
            ads_dict['metadata']['X-Parsed-By'].append(unary_dict['X-Parsed-By'])

            out_f.write(json.dumps(ads_dict))
            out_f.write('\n')
        except Exception as e:
            logger.info('Unary parser failed: %s' % os.path.abspath(f))
            logger.error(e)

    out_f.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    input_parser = parser.add_mutually_exclusive_group(required=True)

    input_parser.add_argument('-i', '--in_file', help='Path to input file')
    input_parser.add_argument('-li', '--in_list', help='Path to input list')
    parser.add_argument('-o', '--out_file', required=True,
                        help='Path to output JSON file')
    parser.add_argument('-l', '--log_file', default='./unary-parser-log.txt',
                        help='Log file that contains processing information. '
                             'It is default to ./unary-parser-log.txt unless '
                             'otherwise specified.')
    parser.add_argument('-p', '--tika_server_url', required=False,
                        help='Tika server URL')
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
    parser.add_argument('-c', '--corenlp_server_url',
                        default='http://localhost:9000',
                        help='CoreNLP Server URL')
    parser.add_argument('-n', '--ner_model', required=False,
                        help='Path to a Named Entity Recognition (NER) model')
    
    parser.add_argument('-cnte', '--containee_model_file',
                    required = True,
                    help='Path to a trained Containee model')
    parser.add_argument('-cntr', '--container_model_file',
                    required = True,
                    help='Path to a trained Container model')
    parser.add_argument('-m', '--entity_linking_method',
                    required = True,
                    choices = [
                        'closest_container_closest_containee',
                        'closest_target_closest_component'
                        'closest_containee',
                        'closest_container',
                        'closest_component',
                        'closest_target'
                    ],
                    help='Method to form relations between entities. '
                    'closest_containee: for each Container instance, link it to its closest Containee instance with a Contains relation'
                    'closest_container: for each Containee instance, link it to its closest Container instance with a Contains relation'
                    'closest_component: for each Container instance, link it to its closest Component instance with a Contains relation'
                    'closest_target: for each Containee instance, link it to its closest Target instance with a Contains relation'
                    'union_closest_containee_closest_container: union the relation instances found by closest_containee and closest_container')

    parser.add_argument('-g', '--gpu_id',
                    default = 0,
                    type = int,
                    help='GPU ID. If set to negative then no GPU would be used.')
    parser.add_argument('-b', '--batch_size',
                    default = 10,
                    type = int, 
                    help='Batch size at inference time.')

    args = parser.parse_args()
    process(**vars(args))

