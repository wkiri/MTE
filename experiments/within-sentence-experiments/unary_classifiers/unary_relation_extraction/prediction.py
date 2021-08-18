# python3
# predict.py
# Mars Target Encyclopedia
# This script extract relations from Container's and Containee's instances.  
#
# Yuan Zhuang
# July 30, 2021
# Copyright notice at bottom of file.


import os, sys, argparse, torch, pickle, random, json, numpy as np
from os.path import abspath, dirname, join, exists
from sys import stdout
from copy import deepcopy 

curpath = dirname(abspath(__file__))

exppath = dirname(dirname(dirname(curpath)))
sharedpath = join(exppath, 'shared')
sys.path.insert(0, sharedpath)
from instance import Rel_Instance, Span_Instance

upperpath = dirname(curpath)
sys.path.insert(0, upperpath)
from config import label2ind, ind2label
from eval import relation_tuple_eval, relation_instance_eval

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

def get_closest_target(targets, components):

    """
    Link each containee to its closest target in the same sentence. 
    """
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
                    elif dist == min_dist:
                        # If there is a tie, choose the preceding target
                        is_closest = closest_tidx[0] > tidx[0]
                    if is_closest:
                        min_dist = dist
                        closest_targetid = target.span_id
                        closest_tidx = tidx

            for target in targets:
                if target.span_id == closest_targetid and component.pred_relation_label == 'Contains':
                    rel = Rel_Instance(target, component)
                    rel.pred_relation_label = 'Contains'
                    new_rels.append(rel)

    return new_rels


def get_closest_component(targets, components):

    """
    for each container, link it to its closest component 
    """
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
                        # break tie by choosing the following component 
                        is_closest = closest_cidx[0] < cidx[0]

                    if is_closest:
                        min_dist = dist
                        closest_cidx = cidx


            for component in components:
                if target.pred_relation_label == 'Contains' and component.sent_start_idx == closest_cidx[0]:
                    rel = Rel_Instance(target, component)
                    rel.pred_relation_label = 'Contains'
                    new_rels.append(rel)

    return new_rels


def get_closest_container(targets, components, break_tie = False, break_tie_by_preceding = False):
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

                    if target.pred_relation_label != 'Contains':
                        continue
                    tidx = (target.sent_start_idx, target.sent_end_idx)
                    dist = get_word_dist(tidx, cidx)
                    is_closest = False
                    if min_dist is None: 
                        is_closest = 1
                    elif dist < min_dist: 
                        is_closest = 1
                    elif dist == min_dist:
                        is_closest = closest_tidx[0] > tidx[0]
                    if is_closest:
                        min_dist = dist
                        closest_targetid = target.span_id
                        closest_tidx = tidx

            for target in targets:
                if target.pred_relation_label == 'Contains' and component.pred_relation_label == 'Contains' and target.sent_start_idx == closest_tidx[0]:
                    rel = Rel_Instance(target, component)
                    rel.pred_relation_label = 'Contains'
                    new_rels.append(rel)
    return new_rels



def get_closest_containee(targets, components):
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

                    if component.pred_relation_label != 'Contains':
                        continue
                    cidx = (component.sent_start_idx, component.sent_end_idx)
                    dist = get_word_dist(tidx, cidx)
                    is_closest = False
                    if min_dist is None: 
                        is_closest = 1
                    elif dist < min_dist: 
                        is_closest = 1
                    elif dist == min_dist:
                            is_closest = closest_cidx[0] < cidx[0]
                    if is_closest:
                        min_dist = dist
                        closest_cidx = cidx

            for component in components:
                if target.pred_relation_label == 'Contains' and component.pred_relation_label == 'Contains' and closest_cidx[0] == component.sent_start_idx:
                    rel = Rel_Instance(target, component)
                    rel.pred_relation_label = 'Contains'
                    new_rels.append(rel)
    return new_rels

def get_closest_target_and_component(targets, components):

    rels1 = get_closest_component(deepcopy(targets),deepcopy(components))
    rels2 = get_closest_target(deepcopy(targets), deepcopy(components))

    seen_rel = set()
    new_rels = []
    for rel in rels1 + rels2:
        if rel.re_id in seen_rel:
          continue
        seen_rel.add(rel.re_id)
        new_rels.append(rel)
    
    return new_rels

def get_closest_container_and_containee(targets, components):

    rels1 = get_closest_containee(deepcopy(targets),deepcopy(components))
    rels2 = get_closest_container(deepcopy(targets), deepcopy(components))

    seen_rel = set()
    new_rels = []
    for rel in rels1 + rels2:
        if rel.re_id in seen_rel:
          continue
        seen_rel.add(rel.re_id)
        new_rels.append(rel)
    
    return new_rels



if __name__ == "__main__":


    parser = argparse.ArgumentParser()
    
    parser.add_argument("--targets",required = True, help = "File that cotnains Container's predictions (e.g., targets.pred)")

    parser.add_argument("--components",required = True, help = "File that contains Contain's predictions (e.g., components.pred)")

    parser.add_argument('--entity_linking_method',
                    required = True,
                    choices = [
                        'closest_container_closest_containee',
                        'closest_target_closest_component',
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
                    'closest_container_closest_containee: union the relation instances found by closest_containee and closest_container')

    parser.add_argument("--outdir",default = "./temp", help = "Output directory to save extracted relations")


    args = parser.parse_args()

    targets = pickle.load(open(args.targets, "rb"))
    
    components = pickle.load(open(args.components, "rb"))
    
    # gold_rels = pickle.load(open(args.gold_rels, "rb"))

    if args.entity_linking_method == 'closest_target':
        new_rels = get_closest_target(targets, components)
    
    elif args.entity_linking_method == 'closest_component':
        new_rels = get_closest_component(targets, components)

    elif args.entity_linking_method == 'closest_container':
        new_rels = get_closest_container(targets, components)
    
    elif args.entity_linking_method == 'closest_containee':
        new_rels = get_closest_containee(targets, components)

    elif args.entity_linking_method == 'closest_container_closest_containee':
        new_rels = get_closest_container_and_containee(targets, components)

    else: # entity_linking_method == 'closest_target_closest_component':
        new_rels = get_closest_target_and_component(targets, components)

   
    if not exists(args.outdir):
        os.makedirs(args.outdir)

    outfile = join(args.outdir, 'relations.pred')
    print(f"Saving predictions to {outfile}")

    with open(outfile, 'wb') as f:
        pickle.dump(new_rels, f)

# Copyright 2021, by the California Institute of Technology. ALL
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
