Files:

- MERA-targets-final.txt: MERA-targets.txt with hand-edits (n=1128)
- MERA-targets-final.gaz.txt: CoreNLP gazette format - created with
  (cat MERA-targets-final.txt | while read line ; do echo "Target $line" ; done ) > MERA-targets-final.gaz.txt
- MERA-targets-final-salient.gaz.txt: Gazette with generic names
  removed (e.g., Contact, Edge, Fine) that were causing spurious hits (n=1106)
- MERA-aliases.csv: Map of verbatim target names (aliases) to canonical names

- MERB-targets-final.txt: MERB-targets.txt, no hand-edits (n=1744)
- MERB-targets-final.gaz.txt: Same process as for MER-A, with MER-B input

Note that these lists contain naming variants so there are fewer
unique Targets present than the number suggests.

-------------------------------------------------------------------
Supporting files:

0. Composed of files that follow:
- MERA-targets.txt: union of MERA-{closeout*,CS-targets,targets-added}.txt files (n=1129)
- MERB-targets.txt: union of MERB-{closeout*,CS-targets,targets-added}.txt files (n=1744)

1. Results from manual review of MER targets (using Mission Manager
reports) in 2019:
- MERA-closeout-targets.txt (n=892)
- MERA-closeout-features.txt (n=7)
- MERB-closeout-targets.txt (n=1315)
  (features are not separated for MER-B)

2. Contact science targets from PDS (informed by #1):
(source: https://pds-geosciences.wustl.edu/mer/urn-nasa-pds-mer_cs_target_list/document/overview.txt)
- mera_cs_target_list.csv ; unique targets stored in MERA-CS-targets.txt
- merb_cs_target_list.csv ; unique targets stored in MERB-CS-targets.txt
Column 4 of the .csv files yields 319 unique Spirit targets and 633
unique Opportunity targets.  Obtained via:
$ cut -f4 -d',' mera_cs_target_list.csv | grep -v "Target Name" | sort | uniq > MERA-CS-targets.txt
$ cut -f4 -d',' merb_cs_target_list.csv | grep -v "Target Name" | sort | uniq > MERB-CS-targets.txt

3. Targets added after manual review of MPF/PHX docs
- MERA-targets-added.txt (n=3)
- MERB-targets-added.txt (n=2)

-------------------------------------------------------------------
Superseded (older) files:

- MER-Maestro-targets.txt: MER targets obtained from Maestro Excel
  spreadsheet 
- MER-Maestro-targets-pruned.txt: MER targets pruned (in some fashion)

