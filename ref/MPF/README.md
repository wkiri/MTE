# Files
- MPF-targets.txt: unique superset of MPF target lists from individual
sources (papers, images) - create by:
  cat MPF-targets-*.txt | sort | uniq  > MPF-targets.txt
- MPF-targets.gaz.txt: CoreNLP gazette format - created with
  (cat MPF-targets.txt | while read line ; do echo "Target $line" ; done ) > MPF-targets.gaz.txt
- MPF-horizon.txt: unique superset of MPF horizon lists from individual
sources (papers, images)
- MPF-location.txt: unique superset of MPF location lists from individual
sources (papers, images)
- MPF-ambiguous.txt: terms that don't have a conclusive category yet
- MPF-aliases.csv: Map of verbatim target names (aliases) to canonical names

## Targets
- MPF-targets-bell-00.txt: Targets from Bell et al. (2000)
- MPF-targets-bridges-99.txt: Targets from Bridges et al. (1999)
- MPF-targets-golomek-99.txt: Targets from Golombek et al. (1999)
- MPF-targets-mcsween-99.txt: Targets from McSween et al. (1999)
- MPF-targets-monster-pan-image.txt: Horizon features from the "monster" 
                                     panorama image
- MPF-targets-smith-97.txt: Targets from Smith et al. (1997)
- MPF-targets-stooke-atlas-12.txt: Targets from Stooke (2012)
- MPF-basilisk-targets.txt: Top 500 suggestions from Basilisk
- MPF-targets-basilisk-keep.txt: Basilisk targets to keep
- MPF-targets-manual.txt: Additional targets found via manual review

## Horizon
- MPF-horizon-golomek-99.txt: Horizon features from Golombek et al. (1999)
- MPF-horizon-monster-pan-image.txt: Targets from the "monster" panorama image

## Locations
- MPF-location-mcsween-99.txt: Nearby location names from McSween et al. (1999)
- MPF-location-monster-pan-image.txt: Nearby location names from the "monster" 
                                      panorama image
- MPF-location-smith-97.txt: Nearby location names from Smith et al. (1997)
- MPF-location-stooke-atlas-12.txt: Nearby location names from Stooke (2012)

## Instruments
- MPF-instruments.txt
- basilisk-instruments.txt: Top 500 suggestions from Basilisk

## Properties
- MPF-property-matt.txt: Matt's annotated properties from 10 documents
- MPF-property-raymond.txt: Raymond's annotated properties from 10 documents
- MPF-property.txt: Unique terms from Matt and Raymond combined

## Other
- basilisk-elements+minerals.txt: Top 500 suggestions from Basilisk

# Images
- monster_pan.jpg: Monster Panorama with names (unattributed)
- stooke-MPF-targets.pdf: Figure from Stooke (2012)

# References

Bell, J.F. III, McSween Jr., H.Y., Crisp, J.A., Morris, R.V., Murchie,
S.L., Bridges, N.T., Johnson, J.R., Britt, D.T., Golombek, M.P.,
Moore, H.J., Ghosh, A., Bishop, J.L., Anderson, R.C., Bruckner, J.,
Economou, T., Greenwood, J.P., Gunnlaugsson, H.P., Hargraves, R.M.,
Hviid, S., Knudsen, J.M., Madsen, M.B., Reid, R., Rieder, R., and
Soderblom, L. (2000). "Mineralogic and compositional properties of
Martian soil and dust: Results from Mars Pathfinder," Journal of
Geophysical Research: Planets, 105(E1), 1721-1755.

Bridges, N.T., Greeley, R., Haldemann, A.F.C., Herkenhoff, K.E.,
Kraft, M., Parker, T.J., and Ward, A.W. (1999). "Ventifacts at the
Pathfinder landing site," Journal of Geophysical Research: Planets,
104(E4), 8595–8615.

Golombek, M.P., Anderson, R.C., Barnes, J.R., Bell III, J.F., Bridges,
N.T., Britt, D.T., Brückner, J., Cook, R.A., Crisp, D., Crisp, J.A.,
Economou, T., Folkner, W.M., Greeley, R., Haberle, R.M., Hargraves,
R.B., Harris, J.A., Haldemann, A.F.C., Herkenhoff, K.E., Hviid, S.F.,
Jaumann, R., Johnson, J.R., Kallemeyn, P.H., Keller, H.U., Kirk, R.L.,
Knudsen, J.M., Larsen, S., Lemmon, M.T., Madsen, M.B., Magalhães,
J.A., Maki, J.N., Malin, M.C., Manning, R.M., Matijevic, J., McSween
Jr., H.Y., Moore, H.J., Murchie, S.L., Murphy, J.R., Parker, T.J.,
Rieder, R., Rivellini, T.P., Schofield, J.T., Seiff, A., Singer, R.B.,
Smith, P.H., Soderblom. L.A., Spencer, D.A., Stoker, C.R., Sullivan,
R., Thomas, N., Thurman, S.W., Tomasko, M.G., Vaughan, R.M., Wänke,
H., Ward, A.W., and Wilson, G.R. (1999). "Overview of the Mars
Pathfinder Mission: Launch through landing, surface operations, data
sets, and science results," Journal of Geophysical Research: Planets,
104(E4), 8523–8553.

McSween Jr., H.Y., Murchie, S.L., Crisp, J.A., Bridges, J.T.,
Anderson, R.C., Bell III, J.F., Britt, D.T., Bruckner, J., Dreibus,
G., Economou, T., Ghosh, A., Golombek, M.P., Greenwood, J.P., Johnson,
J.R., Moore, H.J., Morris, R.V., Parker, T.J., Rieder, R., Singer, R.,
and Wanke, H. (1999) "Chemical, multispectral, and textural
constraints on the composition and origin of rocks at the Mars
Pathfinder landing site," Journal of Geophysical Research: Planets,
104(E4), 8679-8715.

Smith, P.H., Bell III, J.F., Bridges, N.T., Britt, D.T., Gaddis, L., 
Greeley, R., Keller, H.U., Herkenhoff, K.E., Jaumann, R., 
Johnson, J.R., Kirk, R.L., Lemmon, M., Maki, J.N., Malin, M.C.,
Murchie, S.L., Oberst, L., Parker, T.J., Reid, R.J., Sablotny, R.,
Soderblom, L.A., Stoker, C., Sullivan, R., Thomas, N., 
Tomasko, M.G., Ward, W., and Wegryn, E. (1997) "Results from the Mars
Pathfinder Camera," Science, 273(5344), 1758-1765.

Stooke, P. (2012) The International Atlas of Mars Exploration.
