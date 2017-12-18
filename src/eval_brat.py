#!/usr/bin/env python
# evaluate.py
# Evaluate IE results (named entities and relations),
# given annotations that are stored in brat-format .ann files.
# Brat format: http://brat.nlplab.org/standoff.html
#
# Kiri Wagstaff
# July 31, 2017
# Copyright notice at bottom of file.

import sys, os, re, string
from brat_annotation import BratAnnotation
# named entity: Target with start, end
# relation: Event with self.targets, self.cont lists

def usage():
    print './eval_brat.py <annotation_dir> <groundtruth_dir>'
    sys.exit(1)


# Read in the annotations from a brat .ann file and return in a list
def read_file_annots(fn, doc_id):
    annots = []
    with open(fn, 'r') as f:
        for line in f.readlines():
            annots.append(BratAnnotation(line, doc_id, 'system'))
    return annots


# Read in all of the annotations in a directory and return in a list
def read_dir_annots(dirname):
    dirlist = [fn for fn in os.listdir(dirname) if
               fn.endswith('.ann')]
    dirlist.sort()
    # testing: First one only
    #dirlist = [dirlist[0]]
    #dirlist = dirlist[0:2]

    all_annots = []
    for fn in dirlist:
        fullname = os.path.join(dirname, fn)

        # Assumes conf (e.g., 'lpsc15') is the first item in the dirname.
        # Admittedly, this is brittle!
        doc_id = dirname.split('/')[-2].split('-')[0] + '-' + fn[:-4]

        # Result is a flat list.  This is okay because each 
        # document's annotations track which doc they came from (if needed).
        all_annots += read_file_annots(fullname, doc_id)

    return all_annots


def compute_recall(annots_sys, annots_gt, ne):
    corr = 0

    nes_sys = [a for a in annots_sys \
                   if a.label == ne and a.type == 'anchor']
    nes_gt  = [a for a in annots_gt  \
                   if a.label == ne and a.type == 'anchor']

    # For each nes_gt annotation, look for a match in nes_sys
    for ne_gt in nes_gt:
        match = [n for n in nes_sys \
                     if (n.doc_id == ne_gt.doc_id and
                         n.start  == ne_gt.start and
                         n.end    == ne_gt.end)]
        if len(match) == 1:
            corr += 1
        elif len(match) > 1:
            print 'Error: more than one match with the same type.'
            print ne_gt, [(m.start, m.end, m.name) for m in match]
        '''
        else:
            print 'No match for',  ne_gt
        '''

    if len(nes_gt) == 0:
        return corr, len(nes_gt), 0.0
    else:
        return corr, len(nes_gt), corr * 100.0 / len(nes_gt)


def compute_precision(annots_sys, annots_gt, ne):
    corr = 0

    nes_sys = [a for a in annots_sys \
                   if a.label == ne and a.type == 'anchor']
    nes_gt  = [a for a in annots_gt  \
                   if a.label == ne and a.type == 'anchor']

    # For each nes_sys annotation, look for a match in nes_gt:
    for ne_sys in nes_sys:
        match = [n for n in nes_gt \
                     if (n.doc_id == ne_sys.doc_id and
                         n.start  == ne_sys.start and
                         n.end    == ne_sys.end)]
        if len(match) == 1:
            corr += 1
        elif len(match) > 1:
            print 'Error: more than one match with the same type.'
            print ne_sys, ne_sys.doc_id, [(m.doc_id, m.start, m.end, m.name) for m in match]

    if len(nes_sys) == 0:
        return corr, len(nes_sys), 0
    else:
        return corr, len(nes_sys), corr * 100.0 / len(nes_sys)


# Evaluate the annotations in dir_sys against those in dir_gt
def eval_brat(dir_sys, dir_gt):
    # Note these tests only work if the script is run in git/src
    """
    >>> eval_brat('test_eval_brat/lpsc16-C-pre-annotate', 'test_eval_brat/lpsc16-C-pre-annotate') # doctest: +NORMALIZE_WHITESPACE
    Read 26 annotations from 1 files in test_eval_brat/lpsc16-C-pre-annotate.
    Read 26 ground-truth annotations from 1 files in test_eval_brat/lpsc16-C-pre-annotate.
                Recall  Prec.   F1
    Element     100.00  100.00  100.00
    Mineral     100.00  100.00  100.00
    Target      100.00  100.00  100.00
    Total:      100.00  100.00  100.00

    >>> eval_brat('test_eval_brat/lpsc16-C-pre-annotate-notarget', 'test_eval_brat/lpsc16-C-pre-annotate') # doctest: +NORMALIZE_WHITESPACE
    Read 25 annotations from 1 files in test_eval_brat/lpsc16-C-pre-annotate-notarget.
    Read 26 ground-truth annotations from 1 files in test_eval_brat/lpsc16-C-pre-annotate.
                Recall  Prec.   F1
    Element     100.00  100.00  100.00
    Mineral     100.00  100.00  100.00
    Target      0.00    0.00    0.00
    Total:      96.15   100.00  98.04

    >>> eval_brat('test_eval_brat/lpsc16-C-pre-annotate', 'test_eval_brat/lpsc16-C-pre-annotate-notarget') # doctest: +NORMALIZE_WHITESPACE
    Read 26 annotations from 1 files in test_eval_brat/lpsc16-C-pre-annotate.
    Read 25 ground-truth annotations from 1 files in test_eval_brat/lpsc16-C-pre-annotate-notarget.
                Recall  Prec.   F1
    Element     100.00  100.00  100.00
    Mineral     100.00  100.00  100.00
    Total:      100.00  100.00  100.00

    >>> eval_brat('test_eval_brat/lpsc16-C-pre-annotate', 'test_eval_brat/lpsc16-C-raymond') # doctest: +NORMALIZE_WHITESPACE
    Read 26 annotations from 1 files in test_eval_brat/lpsc16-C-pre-annotate.
    Read 38 ground-truth annotations from 1 files in test_eval_brat/lpsc16-C-raymond.
                Recall  Prec.   F1
    Element     63.64   70.00   66.67
    Material    0.00    0.00    0.00
    Mineral     83.33   100.00  90.91
    Total:      57.89   88.00   69.84

    >>> eval_brat('test_eval_brat/lpsc16-C-pre-annotate', 'test_eval_brat/lpsc16-C-raymond-v2') # doctest: +NORMALIZE_WHITESPACE
    Read 26 annotations from 1 files in test_eval_brat/lpsc16-C-pre-annotate.
    Read 59 ground-truth annotations from 1 files in test_eval_brat/lpsc16-C-raymond-v2.
                Recall  Prec.   F1
    Element     60.00   60.00   60.00
    Material    0.00    0.00    0.00
    Mineral     68.18   100.00  81.08
    Total:      35.59   84.00   50.00
    """

    # Read in the annotations to be tested
    annots_sys = read_dir_annots(dir_sys)
    print 'Read %d annotations from %d files in %s.' % \
        (len(annots_sys), 
         len(set([a.doc_id for a in annots_sys])), 
         dir_sys)

    # Read in the ground-truth annotations
    annots_gt = read_dir_annots(dir_gt)
    print 'Read %d ground-truth annotations from %d files in %s.' % \
        (len(annots_gt), 
         len(set([a.doc_id for a in annots_gt])), 
         dir_gt)

    # Careful: only evaluate on documents that appear in both sets.
    #sys_files = set([a.doc_id for a in annots_sys])
    #gt_files  = set([a.doc_id for a in annots_gt])
    #annots_gt  = [a for a in annots_gt  if a.doc_id in sys_files]
    #annots_sys = [a for a in annots_sys if a.doc_id in gt_files]
    #print '... now %d system and %d ground-truth files.' % \
    #    (len(set([a.doc_id for a in annots_sys])), 
    #     len(set([a.doc_id for a in annots_gt])))

    gt_only = set([a.doc_id for a in annots_gt]).difference(set([a.doc_id for a in annots_sys]))
    if len(gt_only) > 0:
        print 'Only in ground truth:', gt_only

    # Compute recall and precision for each named entity (NE) type.
    # NEs are marked as 'anchors' here.
    NE_types = sorted(list(set([a.label for a in annots_gt \
                                    if a.type == 'anchor'])))
    # Restrict to ones we care about
    NE_types = ['Element', 
                'Mineral',
                'Target']

    print '\t\tRecall\tPrec.\tF1'
    tot_ncorr  = 0
    tot_ref    = 0
    tot_return = 0
    for ne in NE_types:
        # Compute recall
        (ncorr_r, ntot_r, recall) = compute_recall(annots_sys, annots_gt, ne)

        # Compute precision
        (ncorr_p, ntot_p, precision) = compute_precision(annots_sys, annots_gt, ne)
        assert ncorr_r == ncorr_p

        if recall+precision < sys.float_info.epsilon:
            print '%s\t%.2f\t%.2f\t0.00' \
                % (ne, recall, precision)
        else:
            print '%s\t%.2f\t%.2f\t%.2f' \
                % (ne, recall, precision, 
                   2*recall*precision/(recall+precision))

        tot_ncorr  += ncorr_r
        tot_ref    += ntot_r
        tot_return += ntot_p

    tot_rec  = tot_ncorr * 100.0 / tot_ref if tot_ref > 0 else 0.0
    tot_prec = tot_ncorr * 100.0 / tot_return if tot_return > 0 else 0.0

    if tot_rec+tot_prec < sys.float_info.epsilon:
        print 'Total:\t%.2f\t%.2f\t0.00' \
            % (tot_rec, tot_prec)
    else:
        print 'Total:\t%.2f\t%.2f\t%.2f' \
            % (tot_rec, tot_prec,
               2*tot_rec*tot_prec/(tot_rec+tot_prec))


def main():
    if len(sys.argv) != 3:
        usage()

    eval_brat(sys.argv[1], sys.argv[2])


if __name__ == '__main__':
    '''
    # Run inline tests
    import doctest

    (num_failed, num_tests) = doctest.testmod()
    filename                = os.path.basename(__file__)

    if num_failed == 0:
        print "%-20s All %3d tests passed!" % (filename, num_tests)
    else:
        sys.exit(1)
    '''
    main()


# Copyright 2017, by the California Institute of Technology. ALL
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
