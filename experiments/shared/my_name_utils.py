# python3
# my_name_utils.py
# Mars Target Encyclopedia
# This script contains codes that processes the name of Target and Component.
#
# Yuan Zhuang
# July 30, 2021
# Copyright notice at bottom of file.



import os, re, string, sys
from os.path import abspath, dirname, join

curpath = dirname(abspath(__file__))
srcpath = join(dirname(dirname(curpath)), "src")
sys.path.append(srcpath)

from name_utils import targettab,symtab, canonical_name, canonical_target_name, canonical_property_name

def canonical_elemin_name(name):
    """
    This function gets canonical name for a component (either element/mineral): 
    """
    # remove hypen, unserscore, and extra space 
    name = " ".join(re.sub(r"[-_]", " ",name).split())
    name = " ".join([canonical_name(k) for k in name.split()])
    return name


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