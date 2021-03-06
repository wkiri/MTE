# Per-mission target (and other category) listings
- MER/: Mars Exploration Rovers
- MPF/: Mars Pathfinder
- MSL/: Mars Science Laboratory rover
- PHX/: Mars Phoenix lander

# Final gazettes for NER models (Target + Element + Mineral)
- MPF_targets_minerals-2017-05_elements.gaz.txt - created by:
  cat element-correct-MPF+periodic-table.gaz.txt mineral-correct-MPF+IMA.gaz.txt MPF/MPF-targets.gaz.txt > MPF_targets_minerals-2017-05_elements.gaz.txt
- PHX_targets_minerals-2017-05_elements.gaz.txt - created by:
  cat element-correct-MPF+periodic-table.gaz.txt mineral-correct-MPF+IMA.gaz.txt PHX/PHX-targets.gaz.txt > PHX_targets_minerals-2017-05_elements.gaz.txt
- MERA_targets_minerals-2017-05_elements.gaz.txt - created by:
  cat element-correct-MPF+periodic-table.gaz.txt mineral-correct-MPF+IMA.gaz.txt MER/MERA-targets-final.gaz.txt > MERA_targets_minerals-2017-05_elements.gaz.txt

# Elements
Best list to use is marked with **.
- elements.txt (upper case for proper names + abbreviations)
- elements-use.txt (filtered to omit single-letter abbreviations,
  which are often spurious)
- elements.gaz.txt (elements.txt in "gazette" format for CoreNLP)
- element-total-list.txt (from Basilisk, using LPSC 2014-2016)
- element-correct-list.txt (after human review)
- element-correct-list.gaz.txt (in "gazette" form for use by CoreNLP)
- element-correct-MPF.txt (from Basilisk, using LPSC MPF docs,
  after human review of MPF/basilisk-elements+minerals.txt)
- ** element-correct-MPF+periodic-table.txt (merge MPF + periodic table lists)
- ** element-correct-MPF+periodic-table.gaz.txt (merge MPF + periodic table lists)

# Minerals
Best list to use is marked with **.
- minerals-IMA-2017-05.txt (minerals from IMA_Master_List_2017_05.pdf)
- minerals-IMA-2017-05.gaz.txt (in "gazette" form for use by CoreNLP)
- mineral-total-list.txt (from Basilisk, using LPSC 2014-2016)
- mineral-correct-list.txt (after human review)
- mineral-correct-list.gaz.txt (in "gazette" form for use by CoreNLP; 
  longer because it includes name variants without accents)
- mineral-correct-MPF.txt (from Basilisk, using LPSC MPF docs, 
  after human review of MPF/basilisk-elements+minerals.txt)
- ** mineral-correct-MPF+IMA.txt (merge MPF + IMA lists)
- ** mineral-correct-MPF+IMA.gaz.txt (merge MPF + IMA lists)
- non-minerals.txt (words that end in -ite but aren't minerals, often
due to parse errors)
- minerals.txt (early test file?)

# Instruments
- instruments.txt (union across all missions)

# Properties
- ** properties.txt (union across all missions,
  combining */*-property-final.txt and the following files:)
- property-basilisk-PHX.txt (properties approved from Basilisk's list)
- property-manual-MPF.txt (manually added properties in MPF docs)
