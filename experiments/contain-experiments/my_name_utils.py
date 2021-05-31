import os, re, string 
from os.path import abspath, dirname, join

curpath = dirname(abspath(__file__))
srcpath = join(dirname(dirname(curpath)), "src")
sys.path.append(srcpath)

from nam_utils import targettab,symtab, canonical_name, canonical_target_name, canonical_property_name

def canonical_elemin_name(name):
    """
    Gets canonical name for a component (either element/mineral): title case
    :param name - name whose canonical name is to be looked up
    :return canonical name
    """
	# remove hypen, unserscore, and extra space 
	name = " ".join(re.sub(r"[-_]", " ",name).split())
	name = " ".join([canonical_name(k) for k in name.split()])
	return name