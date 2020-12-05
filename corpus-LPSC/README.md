This directory contains several sets of annotated LPSC abstracts,
suitable for viewing/interaction with the brat tool.

## LPSC 2015:
- lpsc15-C-raymond-sol1159-v3-utf8: Raymond's annotations using 
  targets through sol 1159

## LPSC 2016:
- lpsc16-C-raymond-sol1159-utf8: Raymond's annotations using
  targets through sol 1159

## Experiments: 
- The directory 'experiments-karan' contains jSRE examples generated over multiple experiments
-- lpsc-brat: Used coreNLP old model for entities and brat for relationships
-- lpsc-brat-neg: Used coreNLP old model for entities and brat for relationships with more negative examplples
-- lpsc-brat-neg-no-ref: Used coreNLP new model for entities and brat for relationships with more negative examples
- The directory 'experiments-karan' also contains examples split between train, dev and test

## Other:
- eval-annot-raymond.xlsx: evaluation of the pre-annotate versions
  versus Raymond's annotations

## Deprecated:
- lpsc15-A: relation annotations (contains, contains-high,
  contains-low) 
- lpsc15-B: contains as an event, with confidence and amount
  (high/low) attributes
- lpsc15-C-pre-annotate-sol-707: auto-annotation of targets and elements 
  (abstracts that mention ChemCam only; target list through sol 707)
- lpsc15-C-raymond-sol-707: Raymond's annotations of docs from 
  lpsc15-C-pre-annotate-sol-707
- lpsc15-C-pre-annotate-sol-1159: auto-annotation of Element, Mineral,
  and Targets
  (abstracts that mention ChemCam only; target list through sol 1159)
- lpsc15-C-raymond-sol-1159: Raymond's manual annotations
  (edits to the pre-annotate versions)
- lpsc15-C-raymond-sol-1159-v2: Raymond's second pass
- lpsc15-C-pre-annotate-sol-1159-v3: auto-annotation with latest
  pre_annotate.py script.  Raymond didn't use these versions, but they
  demonstate the output that can be achieved using keywords/lists.
- lpsc16-C-pre-annotate: auto-annotation of Element, Mineral,
  and Targets (abstracts that mention ChemCam only)
- lpsc16-C-raymond: Raymond's manual annotations
  (edits to the pre-annotate versions)
