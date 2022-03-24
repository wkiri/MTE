The Mars Target Encyclopedia (MTE) is a collection of Mars mission
targets (i.e., named rocks and soils) associated with scientific
publications.  The goal is to enable literature searches for a given
target as well as to identify targets with similar reported
properties.  Each mention (occurrence of a target name) is recorded in
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
searches and joins across the tables.  Please see mte_schema.jpg for a
visual depiction of the relationships between tables.

- targets.csv: Table listing all targets that appear in the document
  collection.  This is not an official mission target list.  Only
  targets that appear in the MTE document collection are included.
  Target names in this table may include abbreviations  and
  misspellings, according to how the targets appear in the source
  documents.  See the aliases table to obtain the mapping between
  target name variations and the canonical target name.

  Fields include the target id, target name, and mission code.  
  * The target name, for consistency, encodes spaces as underscores,
  capitalizes the first letter of each word, and ensures terminal
  numbers are separated from the name by an underscore.
  * The mission code is "mpf", "phx", or "mer2" (Spirit).
  * The target id consists of the target name, a hyphen, and the mission
  code.  It allows disambiguation when a target name is used
  independently by more than one mission.

- aliases.csv: Table linking target name variants (as they appear in a
  document, standardized as above) to a canonical target name.  This
  allows the identification of all content relevant to a target, which
  might span multiple target names, such as typos like "Commanche" for
  "Comanche" and abbreviations like "Hmp" for "Humphrey."  Alias
  identification was done by inspecting the source documents for
  context.  Canonical names were chosen based on frequency of
  appearance in the literature, naming conventions used by each
  mission, and consultation with mission scientists.

  Note: For completeness, all aliased canonical target names appear in
  the targets table, even when they did not appear verbatim in the
  documents (e.g., Green_Eyes is included as a target name, even
  though it only appeared as Greeneyes in the documents).  Therefore,
  a small number of target names do not appear in the mentions table,
  which includes all occurrences of target names in the documents.

Target occurrences (mentions) in sentences and documents:

- documents.csv: Table containing information about each source
  publication (currently LPSC abstracts).  Fields include the document
  id, which consists of the year of publication, an underscore, and
  the LPSC abstract number; the abstract number; title; the authors (a
  comma separated list, so it is enclosed in double-quotes for
  parsing); the primary author's last name; the year of publication;
  venue (a quoted string with the conference name and abstract
  number); and document URL.

- sentences.csv: Table enumerating sentences with relevant content
  (e.g., targets, components, properties).  Fields include the
  document id (as above), the sentence id, and the verbatim sentence.
  The sentence id consists of the document id followed by a hyphen and
  the index of the sentence in the document.  If the sentence contains
  a comma, it is enclosed in double-quotes.  Any internal
  double-quotes (") were converted to two single-quotes ('') to meet
  PDS requirements.

- mentions.csv: Table linking targets to each source sentence in
  which that target is mentioned.  If a target occurs more than once
  in a sentence, that sentence appears only once in this table.
  Fields include target id (as above) and sentence id (as above).
  between missions.

Target composition and properties:

Note: As much as possible, we avoid making interpretations of author
intent and instead preserve components and properties as they appear
in the source document.  Therefore, singular and plural forms as well
as abbreviations and alternate spellings may appear in the component
and property lists.

- components.csv: Table containing names of elements and minerals.
  Fields include the "canonical" component name (e.g., Mn -> Manganese)
  and the component label (Element or Mineral).  We reserve Element for
  items in the periodic table, and use Mineral for more complex
  entities or measurements, including terms such as NpOx and FeOT.

- properties.csv: Table containing unique property names.  Each property
  name is stored in all lower case with spaces between words.

- contains.csv: Table linking targets to components.  Fields include
  the target id (as above), component name (as above), and two sentence
  ids (as above) for the location of the target and the component.
  For a relation that crosses sentences, the two sentence ids will
  differ.  If the target and component appear in the same sentence,
  the two sentence ids are the same. 

- has_property: Table linking targets to properties.  Fields include
  the target id (as above), property name (as above), and two sentence
  ids (as above) for the location of the target and property.

Methods
-------
  
For information on the underlying methods used to find and extract
target information in text documents, see reference [1] below.
Automated text analysis methods were accompanied by manual review of
the extracted information.  See reference [2] for additional details
and a summary of content specific to the Mars Pathfinder and Mars
Phoenix Lander missions and reference [3] for content specific to the
Spirit Mars Exploration Rover.

Citation
--------

If you use the contents of the Mars Target Encyclopedia in your own
work, please include this citation:

Kiri Wagstaff, Raymond Francis, Matthew Golombek, Steven Lu, Ellen
Riloff, and Leslie Tamppari. (2021). Mars Target Encyclopedia (Version
2.0) [Data set]. http://doi.org/10.17189/1520763

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

3. Targets from the Spirit Mars Exploration Rover in the Mars Target
Encyclopedia. 
Kiri L. Wagstaff, Raymond Francis, Matthew Golombek, Steven Lu, Ellen
Riloff, Leslie Tamppari, Yuan Zhuang, and Thomas C. Stein.
53rd Lunar and Planetary Science Conference, Abstract #1231, March
2022.
  https://wkiri.com/research/papers/wagstaff-mte-lpsc-22.pdf

--------------------------------------------------
Contact: Kiri Wagstaff, Jet Propulsion Laboratory,
kiri.wagstaff@jpl.nasa.gov

Team: Kiri Wagstaff, Raymond Francis, Matthew Golombek, Steven Lu,
Ellen Riloff, and Leslie Tamppari 

Funding: Planetary Data Archiving, Restoration, and Tools (PDART)
program
