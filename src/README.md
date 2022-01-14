## MTE Source Code

The MTE parses PDF documents and stores information in a JSONL file.  This file can be used to generate an interactive annotated corpus (e.g., for manual review and editing of the extracted information) and/or an SQLite database to support search queries.

### 1. MTE parser pipeline

The MTE parser pipeline consists of 7 parsers. In this section, only the LPSC and generic paper parsers are introduced because they most likely will be used more frequently than other parsers. To see the details of all parsers, please check the [MTE parser wiki document](https://github.com/wkiri/MTE/wiki/MTE-Parsers). Each parser script contians (1) the actual parsing methods and (2) a "main" function that processes the input documents to the output jsonl file.   


**LPSC Parser**

The LPSC parser is created to process the two-page abstract from Lunar and Planetary Science Conference (LPSC). Once the LPSC parser script is invoked (e.g., calling the `main()` function of the `lpsc_parser.py` script), the following actions will occur in sequential order to process the input docments to the output JSON file.

1. TIKA parser: convert the input documents (in PDF format) to text.
2. ADS parser: query the [ADS database](https://ui.adsabs.harvard.edu/) to populate information including author list, primary author, authors' affiliations, publication venue, publication date, etc.
3. Paper parser: remove/augment the contents of the parsed text that are general to all papers(e.g., translate some UTF-8 punctuation to ASCII, remove hyphens at the end of lines, etc.).
4. LPSC parser: remove contents specific to the LPSC abstract (e.g., abstract id, abstract header, etc.).
5. CoreNLP parser: named entity recognition. 
6. JSRE parser: relation extraction.

To see the command line arguments for `lpsc_parser.py`, please run the following command:

```Console
$ python lpsc_parser.py -h
```

The following command is an example for running `lpsc_parser.py`:

```Console
$ python lpsc_parser.py -li /PATH/TO/LIST/OF/PDF/FILES -o /PATH/TO/OUTPUT/JSONL/FILE -l /PATH/TO/OUTPUT/LOG/FILE -n /PATH/TO/TRAINED/NER/MODEL -jr /PATH/TO/TRAINED/JSRE/MODEL
```

**Paper Parser** 

The paper parser is created to process papers from all publicaiton venues. Once the paper parser script is invoked (e.g., calling the `main()` function of the `paper_parser.py` script), the following actions will occur in sequential order to process the input docments to the output jsonl file.


1. TIKA parser: convert the input documents (in PDF format) to text.
2. ADS parser: query the [ADS database](https://ui.adsabs.harvard.edu/) to populate information including author list, primary author, authors' affiliations, publication venue, publication date, etc.
3. Paper parser: remove/augment the contents of the parsed text that are general to all papers(e.g., translate some UTF-8 punctuation to ASCII, remove hyphens at the end of lines, etc.).
4. CoreNLP parser: named entity recognition. 
5. JSRE parser: relation extraction.

To see the command line arguments for `paper_parser.py`, please run the following command:

```Console
$ python paper_parser.py -h
```

The following command is an example for running `paper_parser.py`:

```Console
$ python paper_parser.py -li /PATH/TO/LIST/OF/PDF/FILES -o /PATH/TO/OUTPUT/JSONL/FILE -l /PATH/TO/OUTPUT/LOG/FILE -n /PATH/TO/TRAINED/NER/MODEL -jr /PATH/TO/TRAINED/JSRE/MODEL
```

**Example use cases**

1. If the documents that we want to process are all from LPSC, then use `lpsc_parser.py`.
2. If the documents that we want to process are from different journals, then use `paper.py`.

### 2. Visualize and review extracted information

The `json2brat.py` script reads the JSON file and writes the content out in the format used by the [brat](https://brat.nlplab.org/) annotation tool.  

```Console
$ python json2brat.py $JSON_FILE $BRAT_DIR
```

The result is a collection in `$BRAT_DIR` that consists of two files for each source document:
* `file.txt`: the parsed text contents for the document
* `file.ann`: brat-format annotations containing entities and relations

After installing brat and putting `$BRAT_DIR` within its `data/` directory, you should be able to browse and interactively edit the annotations.

### 3. Store reviewed information in a database

Once the content has been reviewed, you can generate a final SQLite database by combining the JSON file and reviewed brat `.ann` files.  Assuming you have a `$JSON_FILE` and want to write to `$DB_FILE` for mission `$MISSION$`, create the initial database with:

```Console
$ python ingest_sqlite.py $JSON_FILE -d $DB_FILE -m $MISSION > ingest-DB.log
```

If your documents are from LPSC, please include the `-v lpsc` option to populate the `venue` (including abstract id) and `doc_url` fields for each document:

```Console
$ python ingest_sqlite.py $JSON_FILE -d $DB_FILE -v lpsc -m $MISSION > ingest-DB.log
```

Then update the database with the brat annotations in `$ANN_DIR`, ascribing credit to `$REVIEWER`:

```Console
$ python update_sqlite.py -r $REVIEWER $ANN_DIR $DB_FILE $MISSION -ro > update-DB.log
```

The `-ro` option removes orphaned documents, etc. (i.e., documents that have no relevant targets or relations).

If you have a list of known targets that may include targets that do not occur in at least one document in the collection, but you want them to appear in the `targets` table in the SQLite database, these can be provided in a `$TARGET_LIST` file that contains one target name per row.  Specify this file with the `-tl` option:

```Console
$ python update_sqlite.py -r $REVIEWER $ANN_DIR $DB_FILE $MISSION -ro -tl $TARGET_FILE > update-DB.log
```

Likewise, if you have a list of known target name variants (or aliases), these can be used to populate an `aliases` table in the SQLite database by using the `-a` option, e.g.:

```Console
$ python update_sqlite.py -r $REVIEWER $ANN_DIR $DB_FILE $MISSION -ro -a $ALIAS_FILE > update-DB.log
```

The `$ALIAS_FILE` file should contain one line per alias in the format `alias,canonical_name`.  Users of the database can join `targets` with `aliases` to obtain all search results for a target name and its aliases.

If `-tl` and `-a` are both provided, the mapping in `$ALIAS_FILE` will be used to update the targets in `$TARGET_LIST` by mapping them to their canonical names.  As a result, the total number of target names added to `targets` via `-tl` may be reduced (aliases omitted).  However, the target names that occur in the document collection will be stored verbatim (not remapped to canonical names).  


