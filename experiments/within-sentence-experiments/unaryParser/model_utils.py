# python3
# model_utils.py
# Mars Target Encyclopedia
# This script contains utils for training and testing a model. 
#
# Yuan Zhuang
# July 30, 2021
# Copyright notice at bottom of file.

import sys, os, re
from copy import deepcopy
from os.path import exists 

def add_marker_tokens(tokenizer, ner_labels):
    """
    This function adds entity markers into the tokenizer's vocabulary, such as <ner_start=Target> and <ner_end=Target>
    """
    new_tokens = []
    for label in ner_labels:
        new_tokens.append('<ner_start=%s>'%label.lower())
        new_tokens.append('<ner_end=%s>'%label.lower())
    tokenizer.add_tokens(new_tokens)


def to_device(tensor, gpu_id):
    """
      Move a tensor to a specific gpu depending on self.gpu_id 
    """
    if gpu_id >= 0:
      return tensor.cuda(gpu_id)
    else:
      return tensor

"""
==========================
 inference utils 
==========================
"""
def get_sent2entities(targets, components):
    """
     put targets and components to the corresponding sentence
    """
    sent2entities = {}
    # map to sentence 
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
    """
    get distance between two index tuples. Each index tuple contains (starting index, ending index)
    """
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
                    new_rels.append((target, component))

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
                  new_rels.append((target, component))

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
                  new_rels.append((target, component))
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
                  new_rels.append((target, component))
    return new_rels

def get_closest_target_and_component(targets, components):

    rels1 = get_closest_component(deepcopy(targets),deepcopy(components))
    rels2 = get_closest_target(deepcopy(targets), deepcopy(components))

    seen_rel = set()
    new_rels = []
    for t, c in rels1 + rels2:
        if (t.span_id, c.span_id) in seen_rel:
          continue
        seen_rel.add((t.span_id, c.span_id))
        new_rels.append((t,c))
    
    return new_rels

def get_closest_container_and_containee(targets, components):

    rels1 = get_closest_containee(deepcopy(targets),deepcopy(components))
    rels2 = get_closest_container(deepcopy(targets), deepcopy(components))

    seen_rel = set()
    new_rels = []
    for t, c in rels1 + rels2:
        if (t.span_id, c.span_id) in seen_rel:
          continue
        seen_rel.add((t.span_id, c.span_id))
        new_rels.append((t,c))
    
    return new_rels

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

