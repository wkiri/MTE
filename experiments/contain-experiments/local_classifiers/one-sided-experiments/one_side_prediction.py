import os, sys, argparse, torch, pickle, random, json, numpy as np
from os.path import abspath, dirname, join, exists
from sys import stdout

from copy import deepcopy 

# # test function
curpath = dirname(abspath(__file__))
upperpath = dirname(curpath)
sys.path.append(upperpath)
from instance import Rel_Instance, Span_Instance
from config import label2ind, ind2label
from eval import test_eval, instance_level_eval

def get_sent2entities(targets, components):
    # a pair of target, components from the same sentence if they are predicted with 'Contains' by container and containee resepctively
    sent2entities = {}
    # map to same sentence 
    for t in targets:
        sentid = f"{t.venue},{t.year},{t.docname},{t.sentid}"
        if sentid not in sent2entities:
            sent2entities[sentid] = {
                "Targets":[],
                "Components":[]
            }
        sent2entities[sentid]['Targets'].append(deepcopy(t))
    for c in components:
        sentid = f"{c.venue},{c.year},{c.docname},{c.sentid}"
        if sentid not in sent2entities:
            sent2entities[sentid] = {
                "Targets":[],
                "Components":[]
            }
        sent2entities[sentid]['Components'].append(deepcopy(c))

    return sent2entities
def get_word_dist(idx1, idx2):
    dist = None
    for k in idx1:
        for j in idx2:
            curdist = abs(k - j)
            if dist is None:
                dist = curdist
            else:
                dist = min(dist, curdist)
    return dist

def get_closest_target(targets, components, break_tie = False, break_tie_by_preceding = False):
    sent2entities = get_sent2entities(targets, components)

    new_rels = []
    for sentid in sent2entities:
        components, targets = sent2entities[sentid]['Components'], sent2entities[sentid]['Targets']
        for component in components:
            cidx = (component.sent_start_idx, component.sent_end_idx)
            closest_targetid = None
            closest_tidx = None
            min_dist = None
            if component.pred_relation_label == 'Contains':
                # find closest target and assign
                for target in targets:
                    tidx = (target.sent_start_idx, target.sent_end_idx) 
                    dist = get_word_dist(cidx, tidx)
                    is_closest = False
                    if min_dist is None: 
                        is_closest = 1
                    elif dist < min_dist: 
                        is_closest = 1
                    elif dist == min_dist and break_tie:
                        print("tie!!!")
                        if break_tie_by_preceding:
                            is_closest = closest_tidx[0] > tidx[0]
                        else:
                            is_closest = closest_tidx[0] < tidx[0]
                    if is_closest:
                        min_dist = dist
                        closest_targetid = target.span_id
                        closest_tidx = tidx

            for target in targets:
                rel = Rel_Instance(target, component)
                if target.span_id == closest_targetid and component.pred_relation_label == 'Contains':
                    rel.pred_relation_label = 'Contains'
                else:
                    rel.pred_relation_label = 'O'

                new_rels.append(rel)

    return new_rels


def get_closest_component(targets, components, break_tie = False, break_tie_by_following = False):
    sent2entities = get_sent2entities(targets, components)

    new_rels = []
    for sentid in sent2entities:
        components, targets = sent2entities[sentid]['Components'], sent2entities[sentid]['Targets']
        for target in targets:
            tidx = (target.sent_start_idx, target.sent_end_idx)
            closest_cidx = None
            min_dist = None
            if target.pred_relation_label == 'Contains':
                # find closest target and assign
                for component in components:
                    cidx = (component.sent_start_idx, component.sent_end_idx) 
                    dist = get_word_dist(cidx, tidx)
                    is_closest = False
                    if min_dist is None: 
                        is_closest = 1
                    elif dist < min_dist: 
                        is_closest = 1
                    elif dist == min_dist:
                        if break_tie:
                            if break_tie_by_following:
                                is_closest = closest_cidx[0] < cidx[0]
                            else:
                                is_closest = closest_cidx[0] > cidx[0]
                    if is_closest:
                        min_dist = dist
                        closest_cidx = cidx


            for component in components:
                rel = Rel_Instance(target, component)
                if target.pred_relation_label == 'Contains' and component.sent_start_idx == closest_cidx[0]:
                    rel.pred_relation_label = 'Contains'
                else:
                    rel.pred_relation_label = 'O'

                new_rels.append(rel)

    return new_rels


def pair(targets, components):
    sent2entities = get_sent2entities(targets, components)

    new_rels = []
    for sentid in sent2entities:
        components, targets = sent2entities[sentid]['Components'], sent2entities[sentid]['Targets']
        for t in targets:
            for c in components:
                rel = Rel_Instance(t, c)
                if t.pred_relation_label == 'Contains' and c.pred_relation_label == 'Contains':
                    rel.pred_relation_label = 'Contains'
                else:
                    rel.pred_relation_label = 'O'
                new_rels.append(rel)
    return new_rels


def pair_close_target(targets, components, break_tie = False, break_tie_by_preceding = False):
    sent2entities = get_sent2entities(targets, components)
    new_rels = []
    for sentid in sent2entities:
        components, targets = sent2entities[sentid]['Components'], sent2entities[sentid]['Targets']
        for component in components:
            cidx = (component.sent_start_idx, component.sent_end_idx)
            closest_targetid = None
            closest_tidx = None
            min_dist = None
            if component.pred_relation_label == 'Contains':
                for target in targets:
                    tidx = (target.sent_start_idx, target.sent_end_idx)
                    dist = get_word_dist(tidx, cidx)
                    is_closest = False
                    if min_dist is None: 
                        is_closest = 1
                    elif dist < min_dist: 
                        is_closest = 1
                    elif dist == min_dist and break_tie:
                        if break_tie_by_preceding:
                            is_closest = closest_tidx[0] > tidx[0]
                        else:
                            is_closest = closest_tidx[0] < tidx[0]
                    if is_closest:
                        min_dist = dist
                        closest_targetid = target.span_id
                        closest_tidx = tidx

            for target in targets:
                rel = Rel_Instance(target, component)
                if target.pred_relation_label == 'Contains' and component.pred_relation_label == 'Contains' and target.sent_start_idx == closest_tidx[0]:
                    rel.pred_relation_label = 'Contains'
                else:
                    rel.pred_relation_label = 'O'
                new_rels.append(rel)
    return new_rels



def pair_close_component(targets, components, break_tie = False, break_tie_by_following = False):
    sent2entities = get_sent2entities(targets, components)
    new_rels = []
    for sentid in sent2entities:
        components, targets = sent2entities[sentid]['Components'], sent2entities[sentid]['Targets']
        for target in targets:
            tidx = (target.sent_start_idx, target.sent_end_idx)
            closest_cidx = None
            min_dist = None
            if target.pred_relation_label == 'Contains':
                for component in components:
                    cidx = (component.sent_start_idx, component.sent_end_idx)
                    dist = get_word_dist(tidx, cidx)
                    is_closest = False
                    if min_dist is None: 
                        is_closest = 1
                    elif dist < min_dist: 
                        is_closest = 1
                    elif dist == min_dist and break_tie:
                        if break_tie_by_following:
                            is_closest = closest_cidx[0] < cidx[0]
                        else:
                            is_closest = closest_cidx[0] > cidx[0]
                    if is_closest:
                        min_dist = dist
                        closest_cidx = cidx

            for component in components:
                rel = Rel_Instance(target, component)
                if target.pred_relation_label == 'Contains' and component.pred_relation_label == 'Contains' and closest_cidx[0] == component.sent_start_idx:
                    rel.pred_relation_label = 'Contains'
                else:
                    rel.pred_relation_label = 'O'
                new_rels.append(rel)
    return new_rels

def pair_close_target_and_component(targets, components):

    rels1 = pair_close_component(deepcopy(targets),deepcopy(components))
    rels2 = pair_close_target(deepcopy(targets), deepcopy(components))

    contain_pairs = set([ (rel.span1.span_id, rel.span2.span_id) for rel in rels1 if rel.pred_relation_label == 'Contains'] + [(rel.span1.span_id, rel.span2.span_id) for rel in rels2 if rel.pred_relation_label == 'Contains'])
    new_rels = []
    for t in targets:
        for c in components:
            rel = Rel_Instance(t,c)
            if (t.span_id, c.span_id) in contain_pairs:
                rel.pred_relation_label = 'Contains'
            else:
                rel.pred_relation_label = 'O'
            new_rels.append(rel)
    return new_rels



if __name__ == "__main__":


    parser = argparse.ArgumentParser()
    
    parser.add_argument("-targets",required = True)
    parser.add_argument("-components",required = True)
    parser.add_argument("-gold_rels",required = True)
    parser.add_argument("-analyze",default = 0 )

    parser.add_argument("-mode", choices = ['close_target_bt', 'close_target', 'close_component_bt', 'close_component', 'pair','pair_close_target', 'pair_close_component', 'pair_close_target_bt', 'pair_close_component_bt', 'pair_close_target_and_component'], required = True)


    args = parser.parse_args()
    analyze_dir = join(dirname(abspath(__file__)), "temp/analysis")
    if args.analyze and not exists(analyze_dir):
        os.makedirs(analyze_dir)

    targets = pickle.load(open(args.targets, "rb"))
    components = pickle.load(open(args.components, "rb"))
    gold_rels = pickle.load(open(args.gold_rels, "rb"))

    if args.mode == 'close_target':
        new_rels = get_closest_target(targets, components)
    if args.mode == 'close_target_bt':
        new_rels = get_closest_target(targets, components, break_tie = True, break_tie_by_preceding = True)
    if args.mode == 'close_component':
        new_rels = get_closest_component(targets, components)
    if args.mode == 'close_component_bt':
        new_rels = get_closest_component(targets, components, break_tie = True, break_tie_by_following = True)
    if args.mode == 'pair':
        new_rels = pair(targets, components)
    if args.mode == 'pair_close_target':
        new_rels = pair_close_target(targets, components)
    if args.mode == 'pair_close_target_bt':
        new_rels = pair_close_target(targets, components, break_tie = True, break_tie_by_preceding = True)
    if args.mode == 'pair_close_component':
        new_rels = pair_close_component(targets, components)
    if args.mode == 'pair_close_component_bt':
        new_rels = pair_close_component(targets, components, break_tie = True, break_tie_by_following = True)
    if args.mode == 'pair_close_target_and_component':
        new_rels = pair_close_target_and_component(targets, components)



    precision, recall, f1 = test_eval(new_rels, gold_rels, "Contains")
    print(f"TUPLE-LEVEL EVAL of combined prediction: precison: {precision*100:.2f}, recall: {recall*100:.2f}, f1: {f1*100:.2f}")

    precision, recall, f1 = instance_level_eval(new_rels, gold_rels, "Contains", analyze = args.analyze, analyze_dir = analyze_dir)
    print(f"INSTANCE-LEVEL EVAL of combined prediction: precision: {precision*100:.2f}, recall: {recall*100:.2f}, f1: {f1*100:.2f}")