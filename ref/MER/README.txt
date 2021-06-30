Files:

- MERA-targets.txt (TBD)
- MERB-targets.txt (TBD)

-------------------------------------------------------------------
Supporting files:

1. Results from manual review of MER targets (using Mission Manager
reports) in 2019:
- MERA-closeout-targets.txt
- MERA-closeout-features.txt
- MERB-closeout-targets.txt (TBD)
- MERB-closeout-features.txt (TBD)

2. Contact science targets from PDS (informed by #1):
(source: https://pds-geosciences.wustl.edu/mer/urn-nasa-pds-mer_cs_target_list/document/overview.txt)
- mera_cs_target_list.csv ; unique targets stored in MERA-CS-targets.txt
- merb_cs_target_list.csv ; unique targets stored in MERB-CS-targets.txt
Column 4 of the .csv files yields 319 unique Spirit targets and 633
unique Opportunity targets.  Obtained via:
$ cut -f4 -d',' mera_cs_target_list.csv | grep -v "Target Name" | sort | uniq > MERA-CS-targets.txt
$ cut -f4 -d',' merb_cs_target_list.csv | grep -v "Target Name" | sort | uniq > MERB-CS-targets.txt

3. We also used files from Scott VanBommel (4/14/2021) for additional
vetting of remote sensing targets (MI and Pancam tabs), which are not
included in this repository:
- SolSummary_A.xlsx
- SolSummary_B.xlsx

-------------------------------------------------------------------
Superseded (older) files:

- MER-Maestro-targets.txt: MER targets obtained from Maestro Excel
  spreadsheet 
- MER-Maestro-targets-pruned.txt: MER targets pruned (in some fashion)

