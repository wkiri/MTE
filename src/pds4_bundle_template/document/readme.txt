The Mars Target Encyclopedia (MTE) is a collection of Mars mission
targets (i.e., named rocks and soils) associated with scientific
publications.  The goal is to enable literature searches for a given
target as well as to identify targets with similar reported
properties.  Each mention (target name occurrence) is recorded in
the "mentions" table for a given mission and associated with the
source sentence (for context) as well as the source document (with
URL).  Additional information about target properties such as
composition is also captured.

Note that the MTE captures only the information that is reported in
publications, not instrument data or observations.  The MTE therefore
reflects the selectivity employed by the community in deciding what
information to highlight in a publication.

Currently, the MTE encompasses publications from the Lunar and
Planetary Science Conference from 1998 to 2020.  Future updates
are planned that will included content from peer-reviewed journal
articles as well.

Bundle contents
---------------

The MTE consists of a relational database that links targets to
publications.  In this PDS bundle, the relational database for each
mission is expressed as several .csv files, one per table in the
database.  These tables can be used independently or read in to enable
searches and joins across the tables.

- documents.csv: Table containing information about each source
  publication.  Fields include the document id, which consists of the
  year of publication, an underscore, and the abstract number; the abstract
  number; title; the authors (a comma separated list, so it is enclosed
  in double-quotes for parsing); the primary author's last name; the
  year of publication; venue (a quoted string with the conference name
  and abstract number); and document URL.

- mentions.csv: Table linking target ids to each source sentence in
  which that target is mentioned.  The target id consists of the
  target name, a hyphen, and a mission code (e.g., "mpf" or "phx") to
  disambiguate if target names are re-used between missions.  The
  sentence id consists of the document id followed by a hyphen and the
  index of the sentence in the document.

- sentences.csv: Table enumerating sentences with relevant content
  (e.g., targets, components, properties).  Fields include the
  document id (as above), the sentence id (as above), and the verbatim
  sentence.  If the sentence contains a comma, it is enclosed in
  double-quotes.  Any internal double-quotes (") were converted to two
  single-quotes ('') to meet PDS requirements.

- targets.csv: Table listing all targets.  Fields include the target
  id (as above), the target name (with spaces represented as
  underscores), and the mission code (as above).

  Note: not all targets have mentions.  Only targets that are referred
  to by name in one of the contributing documents will appear in the
  'mentions' table.  For completeness, the targets table includes all
  targets named by each mission, which can also highlight targets
  that lack representation in the literature.

Target composition and properties:

- components.csv: Table containing names of elements and minerals.
  Fields include the "canonical" component name (e.g., Mn -> Manganese)
  and the component label (Element or Mineral).

- properties.csv: Table containing unique property names.  Each property
  is stored in all lower case with spaces between words.

- contains.csv: Table linking targets to components.  Fields include
  the target id (as above), component name (as above), and sentence
  ids (as above) for the location of the target and the component.  If
  they appear in the same sentence, the sentence ids are the same.

- has_property: Table linking targets to properties.  Fields include
  the target id (as above), property name (as above), and sentence ids
  (as above) for the location of the target and property.

Methods
-------
  
For information on the underlying methods used to find and extract
target information in text documents, see reference [1] below.
Automated text analysis methods were accompanied by manual review of
the extracted information.  See reference [2] for additional details
and a summary of content specific to the Mars Pathfinder and Mars
Phoenix Lander missions that appear in this bundle.

Citation
--------

If you use the contents of the Mars Target Encyclopedia in your own
work, please include this citation:

Kiri Wagstaff, Raymond Francis, Matthew Golombek, Steven Lu, Ellen
Riloff, and Leslie Tamppari. (2021). Mars Target Encyclopedia (Version
1.2) [Data set]. http://doi.org/10.17189/1520763

References
----------

1. Mars Target Encyclopedia: Rock and Soil Composition Extracted from
the Literature.
Kiri L. Wagstaff, Raymond Francis, Thamme Gowda, You Lu, Ellen Riloff,
Karanjeet Singh, and Nina L. Lanza.
Proceedings of the Thirtieth Annual Conference on Innovative
Applications of Artificial Intelligence, p. 7861-7866, 2018.
   https://ojs.aaai.org/index.php/AAAI/article/view/11412/11271

2. The Mars Target Encyclopedia Now Includes Mars Pathfinder and Mars
Phoenix Targets.
Kiri L. Wagstaff, Raymond Francis, Matthew Golombek, Steven Lu, Ellen
Riloff, Leslie Tamppari, and Thomas C. Stein.
52nd Lunar and Planetary Science Conference, Abstract #1278, March
2021.
  https://wkiri.com/research/papers/wagstaff-mte-lpsc-21.pdf

--------------------------------------------------
Contact: Kiri Wagstaff, Jet Propulsion Laboratory,
kiri.wagstaff@jpl.nasa.gov

Team: Kiri Wagstaff, Raymond Francis, Matthew Golombek, Steven Lu,
Ellen Riloff, and Leslie Tamppari 

Funding: Planetary Data Archiving, Restoration, and Tools (PDART)
program

