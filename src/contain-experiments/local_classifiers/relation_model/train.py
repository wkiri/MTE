import os, sys, argparse, torch, pickle, random, json, numpy as np
from os.path import abspath, dirname, join, exists
from transformers import *
from torch.utils.data import DataLoader
from sys import stdout
from copy import deepcopy

from evaluation import test_eval, instance_level_eval
# # test function
from predict import predict

from remodel import REModel
from redataset import REDataset, re_collate

curpath = dirname(abspath(__file__))
upperpath = dirname(curpath)
sys.path.append(upperpath)
from instance import Rel_Instance
from config import label2ind, ind2label

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def seed_everything(seed):
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True

def analayze(pred_instances, val_gold_rels, dev_analysis_outdir, label_to_eval):

    signature_to_predins = {}
    for rel in pred_instances:
        if rel.signature not in signature_to_predins:
            signature_to_predins[rel.signature] = []
        signature_to_predins[rel.signature].append(rel)

    gold_signatures = set([rel.signature for rel in val_gold_rels if rel.label == label_to_eval])

    # predict gold contain to none contain
    contain2none_file = join(dev_analysis_outdir, "goldcontain2none.txt")
    with open(contain2none_file, "w") as f:
        for gold_rel in val_gold_rels:
            if gold_rel.label == label_to_eval:

                if gold_rel.signature not in signature_to_predins:
                    f.write(f"MISSING in prediction:\n{str(rel)}\n\n")
                    continue
                for rel in signature_to_predins[gold_rel.signature]:
                    if rel.label == label_to_eval and rel.pred_label != label_to_eval:
                        f.write(f"{str(rel)}\n\n")


    none2contain_file = join(dev_analysis_outdir, "none2contain_file.txt")
    with open(none2contain_file, "w") as f:
        for rel in pred_instances:
            if rel.signature not in gold_signatures and  rel.pred_label == label_to_eval:
                f.write(f"{str(rel)}\n\n")

# evaluate a trained model over validation set and save if achieves better performance 
def eval_and_save(model, val_dataloader, val_gold_rels,  best_f1, args, label_to_eval = "Contains", tuple_eval = False, save_prediction = False): 

    print("\n\n---------------eval------------------\n")
    pred_instances = predict(model, val_dataloader)

    should_save = 0

    if tuple_eval:
        precision, recall, f1 = test_eval(pred_instances, val_gold_rels, label_to_eval)

        score_str = f"TUPLE-LEVEL Evaluation: precision: {precision*100:.2f}, recall: {recall*100:.2f}, f1: {f1*100:.2f}, best f1: {best_f1}\n"
        
        # also check the performance of contain relation for element and mineral at instance level: check how many in-relation objects are identified as in relations

        in_relation_goldspanids = set()
        for rel in val_gold_rels:
            in_relation_goldspanids.add(rel.span2.span_id)

        in_relation_predspanids = set()
        for rel in pred_instances:
            if rel.pred_relation_label == "Contains":
                in_relation_predspanids.add(rel.span2.span_id)
        num_correct = len(in_relation_goldspanids.intersection(in_relation_predspanids))

        span_rec = num_correct / len(in_relation_goldspanids)
        span_pre = num_correct / len(in_relation_predspanids) if len(in_relation_predspanids) != 0 else 0

        span_f1 = 2 * span_rec * span_pre / (span_pre + span_rec) if span_pre + span_rec != 0 else 0 
        print(f"=== OBJECT RELATION INVOLVEMENT (INSTANCE LEVEL): precision = {span_pre}, recall = {span_rec}, f1 = {span_f1}")
        print()


        # TUPLE level: check how many in-relation objects are identified as in relations
        in_relation_goldspans = set()
        for rel in val_gold_rels:
            in_relation_goldspans.add((rel.span2.doc_id, rel.span2.std_text))

        in_relation_predspans = set()
        for rel in pred_instances:
            if rel.pred_relation_label == "Contains":
                in_relation_predspans.add((rel.span2.doc_id, rel.span2.std_text))
        num_correct = len(in_relation_goldspans.intersection(in_relation_predspans))

        span_rec = num_correct / len(in_relation_goldspans)
        span_pre = num_correct / len(in_relation_predspans) if len(in_relation_predspans) != 0 else 0

        span_f1 = 2 * span_rec * span_pre / (span_pre + span_rec) if span_pre + span_rec != 0 else 0 
        print(f"=== OBJECT RELATION INVOLVEMENT (TUPLE LEVEL): precision = {span_pre}, recall = {span_rec}, f1 = {span_f1}")
        print()
    else:
        precision, recall, f1 = instance_level_eval(pred_instances, val_gold_rels, label_to_eval)

        score_str = f"INSTANCE-LEVEL Evaluation: precision: {precision*100:.2f}, recall: {recall*100:.2f}, f1: {f1*100:.2f}, best f1: {best_f1}\n"
        

    

    if best_f1 is None or f1 > best_f1:
        best_f1 = f1
        should_save = 1

    print(f"------------ Evaluation ------------\n\n{score_str}\n")

    # save model now 
    if should_save and args.save_model:

        if not os.path.exists(args.model_save_dir):
            os.makedirs(args.model_save_dir)

        print(f"\nsaving model to {args.model_save_dir}\n")
   
        torch.save(model.state_dict(), join(args.model_save_dir, args.model_save_name + ".ckpt"))


        # write model setting
        with open(join(args.model_save_dir, args.model_save_name + ".config"), "a") as f:
            f.write(f"{args}\n")

        # if args.analyze_dev:
        #     dev_analysis_outdir = args.model_save_dir
        #     analayze(pred_instances, val_gold_rels, dev_analysis_outdir, label_to_eval)
    if save_prediction:
        with open(join(args.model_save_dir, f"{args.mode}.rels.pred"), "wb") as f:
            pickle.dump(pred_instances, f)
    return best_f1

def train(model, train_dataloader, val_dataloader, val_gold_rels, args):

    model.to(device)

    num_batches = len(train_dataloader)

    # FIXME: use different learning rate for LM and other parameters
    """ optimizer """
    param_optimizer = list(model.named_parameters())


    no_decay = ['bias', 'LayerNorm.bias', 'LayerNorm.weight']

    optimizer_grouped_parameters = [
               {'params': [p for n, p in param_optimizer if not any(nd in n for nd in no_decay) and p.requires_grad], 'weight_decay': 0.01},
               {'params': [p for n, p in param_optimizer if any(nd in n for nd in no_decay) and p.requires_grad ], 'weight_decay': 0.0}
          ]

    optimizer = AdamW(optimizer_grouped_parameters,
                              lr=args.lr, correct_bias=False)

    """ scheduler """
    num_training_steps = len(train_dataloader) * args.epoch
    num_warmup_steps = int(0.1 * num_training_steps)


    scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=num_warmup_steps, num_training_steps=num_training_steps)  # PyTorch scheduler


    best_f1 = None
    loss_funct = torch.nn.CrossEntropyLoss()

    for epoch in range(args.epoch):
        avg_loss = 0
        model.train()
        
        for batch_i, train_item in enumerate(train_dataloader):


            logits = model.forward(train_item)

            loss = loss_funct(logits, train_item
            ["labels"].to(device))


            stdout.write(f'\r{epoch}/{args.epoch} epoch: batch = {batch_i}/{num_batches} batch, batch loss = {loss.item():.2f}')
            stdout.flush()

            avg_loss += loss.item()

            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), args.max_grad_norm)
            
            optimizer.step()
            scheduler.step() 
        
            optimizer.zero_grad()

        print("\n\n---------------------------------\n")
        print(f"\n{epoch} epoch avg loss: {avg_loss/num_batches:.2f}\n\n")
        
        print("eval over val ... ")
        args.save_model = 1
        best_f1 = eval_and_save(model, val_dataloader, val_gold_rels,best_f1, args)

        if avg_loss/num_batches < args.early_stop_loss: 
            print("Early stop !")
            break


        

    print("Training ends ! \n")
    return model


if __name__ == "__main__":


    """ ================= parse =============== """
    parser = argparse.ArgumentParser()
    
    # I/O
    parser.add_argument('-mode', choices = ["Merged", "EM", "E", "M"], help = "what experiments to run (e.g., elements, minerals, and their merged set)", required= True)

    parser.add_argument("-train_dir", required = True)
    parser.add_argument("-val_dir", required = True)
    parser.add_argument("-test_dir", default = None, help = "diretory that contains test examples to predict")
    parser.add_argument("-test_evals", default = None, help = "test set for eval")

    parser.add_argument("-analyze_dev", default = False)

    parser.add_argument("-predict_with_extracted_gold_entities", default = 0, type = int, choices = [0,1])


    parser.add_argument("-encoder_dimension", default = 768, type = int)

    parser.add_argument("-dropout_prob", default = 0, type = float)
    parser.add_argument("-fix_bert", default = 0, type = int, choices = [0,1])



    # training setting
    parser.add_argument("-seed", help = "seed", default = 100, type = int)

    parser.add_argument("-epoch", help = "number epochs to train", default = 10, type = int)

    parser.add_argument("-lr", default = 0.00001, type = float)
    
    parser.add_argument("-save_model", help = "whether to save the model or not", default = 1, type = int, choices = [0,1])

    parser.add_argument("-model_save_dir", default = "saved_model", help = "where to save the model to")
    
    parser.add_argument("-model_save_name", default = "trained_model", help = "name the model to be saved")

    parser.add_argument("-batch_size", type = int, default = 16, help = "batch size")
    
    parser.add_argument("-shuffle", type = int, default = 1, choices = [1,0], help = "whether to shuffle the training data in each training epoch")

    parser.add_argument("-max_grad_norm", default = 1.00, type = float, help = "max gradient norm to clip")

    parser.add_argument("-early_stop_loss", default = 0, type = float)


    args = parser.parse_args()

    args.num_classes = len(label2ind)
    seed = args.seed
    seed_everything(seed)
    mode = args.mode
    print(">>> loading data ")
    # load data, this set is instance based training set 
    with open(join(args.train_dir, f"{mode}.extracted_gold_relins.pkl"), "rb") as f:
        train_rels = pickle.load(f)
        pos = [r.label for r in train_rels if r.label != "O" ]
        print(f"Training set contains {len(pos)}/{len(train_rels)}({len(pos)/len(train_rels):.2f}) positive instances ")


    with open(join(args.val_dir, f"{mode}.extracted_gold_relins.pkl"), "rb") as f:
        val_rels = pickle.load(f)


    with open(join(args.val_dir, f"{mode}.annotated_gold_relins.pkl"), "rb") as f:
        val_gold_rels = pickle.load(f)

    if args.predict_with_extracted_gold_entities:        
        print("using gold entities for evaluation")
        test_file = join(args.test_dir, f"{mode}.extracted_gold_relins.pkl")

    else:
        print("using system entities for evaluation")
        test_file = join(args.test_dir, f"{mode}.extracted_system_relins.pkl")

    with open(test_file, "rb") as f:
        test_rels = pickle.load(f)


    with open(join(args.test_dir, f"{mode}.annotated_gold_relins.pkl"), "rb") as f:
        test_gold_rels = pickle.load(f)
    
#     """ ================ make dataset ================ """

    print(">>> making dataset ... ")
    train_dataset = REDataset(train_rels)
    val_dataset = REDataset(val_rels)
    test_dataset = REDataset(test_rels)

#     """ ================ make dataloader ============= """

    print(">>> making data loader ...")
    batch_size = args.batch_size

    train_dataloader = DataLoader(train_dataset, batch_size = args.batch_size, shuffle = args.shuffle, collate_fn = re_collate)

    val_dataloader = DataLoader(val_dataset, batch_size = args.batch_size, collate_fn = re_collate)

    test_dataloader = DataLoader(test_dataset, batch_size = args.batch_size, collate_fn = re_collate)


#     # """ ================ model ================ """

    model = REModel(args)

#     # """ ================ train ================ """
    print("start training ")
    model = train(model, train_dataloader, val_dataloader, val_gold_rels,args)

    print("eval over test ... ")
    args.model_save_dir = join(args.model_save_dir, "test")
    args.analyze_dev = 1
    eval_and_save(model, test_dataloader, test_gold_rels, None, args, tuple_eval = False, save_prediction = False)
    eval_and_save(model, test_dataloader, test_gold_rels, None, args, tuple_eval = True, save_prediction = True)

