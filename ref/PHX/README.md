# Files
- PHX-targets.txt: unique superset of PHX target lists from individual sources
  cat PHX-targets-*.txt | sort | uniq  > PHX-targets.txt
- PHX-targets.gaz.txt: CoreNLP gazette format - created with
  (cat PHX-targets.txt | while read line ; do echo "Target $line" ; done ) > PHX-targets.gaz.txt
- PHX-property.txt: unique superset of PHX property lists from individual sources
- PHX-aliases.csv: Map of verbatim target names (aliases) to canonical names

## Targets
- PHX-targets-arvidson-2009.txt: Targets from Arvidson et al. (2009)
- targets-phx.lexicon: Top 500 suggestions from Basilisk
- PHX-targets-basilisk-keep.txt: Basilisk targets to keep
- PHX-targets-manual.txt: Additional targets found via manual review

## Instruments
- PHX-instruments.txt
- instruments-phx.lexicon: Top 500 suggestions from Basilisk

## Properties
- PHX-property-arvidson-2009.txt: Properties from Arvidson et al. (2009)
- properties-phx.lexicon: Top 500 suggestions from Basilisk

## Other
- elements+minerals-phx.lexicon: Top 500 suggestions from Basilisk

# References
Arvidson, R. E., et al. (2009), "Results from the Mars Phoenix Lander Robotic Arm experiment," J. Geophys. Res., 114, E00E02, doi:10.1029/2009JE003408.
