Target listings:
- MER-targets.txt: MER targets obtained from Maestro Excel spreadsheet

- chemcam-targets-sol1159.txt: ChemCam targets obtained from msl_ccam_obs.csv
  (through sol 1159; use this one)
- chemcam-targets-sol0707.txt: ChemCam targets obtained from msl_ccam_obs.csv
  (through sol 707; included for reference in prior work)

Source:
http://pds-geosciences.wustl.edu/msl/msl-m-chemcam-libs-4_5-rdr-v1/mslccm_1xxx/document/msl_ccam_obs.csv

To generate this list:
cut -f6 -d',' ~/Research/IMBUE/data/chemcam/msl_ccam_obs.csv | grep -v
Target | sort | uniq | wc -l

Elements: 
- elements.txt (upper case for proper names + abbreviations)
