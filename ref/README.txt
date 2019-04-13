Target listings:

1. MER:
- MER-targets.txt: MER targets obtained from Maestro Excel spreadsheet

2. MSL:
- chemcam-targets-sol2224.txt: Through sol 2224 (November 2018)
  (from Fred Calef, MSL_CCAM_targets_sol2346_loco.csv)
- chemcam-targets-sol1647.txt: Through sol 1647 (March 2017)
  (from Geosciences Node CCAM file, see below; applies to all earlier too)
- chemcam-targets-sol1514.txt: Through sol 1514 (November 2016)
- chemcam-targets-sol1159.txt: Through sol 1159 (November 2015)
- chemcam-targets-sol0707.txt: Through sol 707 (August 2014)

Source:
http://pds-geosciences.wustl.edu/msl/msl-m-chemcam-libs-4_5-rdr-v1/mslccm_1xxx/document/msl_ccam_obs.csv

To get a text listing, pull out column 6 and omit the word "Target":
cut -f6 -d',' ~/Research/IMBUE/data/chemcam/msl_ccam_obs.csv | grep -v
Target | sort | uniq | wc -l

Note:
I manually added 16 targets to the lists starting with sol 1159.
These are cases where the target names don't exist in their base form,
although numbered variants (that don't end with _N) do.  To wit:

Bagnold_Dune
Bonanza_King
Confidence_Hills
Ibex_Pass
John_Klein
Mojave2
Mojave
Mont_Wright
Rocknest_3
Ronan
Ruker
Seeley
South_Park
Sutton
Vaqueros
Wallace

Starting with 1514:
Ebony
Hebron
Kapako
Lubango_postsieve
Lubango_presieve
Marimba2_tailings
Marimba_tailings
Mirabib
Peace_Vallis_Fan
Piambo

Starting with 1647:
None

Starting with 2224:
Ailsa_Craig
Balboa
Barby
Bardin_Bluffs
Barn
Bear_Island
Beaver_Brook
Bell_Island
Benner_Hill
Blackrock
Bloodstone_Hill
BonanzaKing
Butchers_Gulley
Clune
Dunes
Dunn_Hill
Frood
Gillespie_Lake
Gobabeb
Goulburn
Greenhorn
Highfield
Ledmore
Macleans_Nose
Marimba2
Marimba_Drill_Hole
Marinba_postsieve
Noriss
Passadumkeag
Podunk
Port_Radium
Red_Cliff
Rock_Hall
Rona
Square_Top
Stirling
Telegraph_Peak
Tindir
Trodday
Voyageurs
Wernecke
Young_Lake

Elements: 
- elements.txt (upper case for proper names + abbreviations)
