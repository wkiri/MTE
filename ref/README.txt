Target listings:

1. MER:
- MER-targets.txt: MER targets obtained from Maestro Excel spreadsheet

2. MSL:
- chemcam-targets-sol1514.txt: Through sol 1514 (November 2016)
- chemcam-targets-sol1159.txt: Through sol 1159 (November 2015)
- chemcam-targets-sol0707.txt: Through sol 707 (August 2014)

Source:
http://pds-geosciences.wustl.edu/msl/msl-m-chemcam-libs-4_5-rdr-v1/mslccm_1xxx/document/msl_ccam_obs.csv

To get a text listing, pull out column 6 and omit the word "Target":
cut -f6 -d',' ~/Research/IMBUE/data/chemcam/msl_ccam_obs.csv | grep -v
Target | sort | uniq | wc -l

Note:
I manually added 7 targets to the sol 1159 and 1514 lists.
These are cases where the target names don't exist in their base form,
although numbered  variants do.  To wit:

Bagnold_Dune
Bonanza_King
Confidence_Hills
Ibex_Pass
John_Klein
Rocknest
Vaqueros

Elements: 
- elements.txt (upper case for proper names + abbreviations)
