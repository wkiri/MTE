## MTE Source Code



### MTE parser pipeline

The MTE parser pipeline consists of 7 parsers. In this section, only the LPSC and paper parsers are introduced because they most likely will be used more frequently than other parsers. To see the details of all parsers, please check the [MTE parser wiki document](https://github.com/wkiri/MTE/wiki/MTE-Parsers). Each parser script contians (1) the actual parsing methods and (2) a "main" function that processes the input documents to the output jsonl file.   


**LPSC Parser**

The LPSC parser is created to process the two-page abstract from Lunar and Planetary Science Conference (LPSC). Once the LPSC parser script is invoked (e.g., calling the `main()` function of the `lpsc_parser.py` script), the following actions will occur in sequential order to process the input docments to the output jsonl file.

1. TIKA parser: convert the input documents (in PDF format) to text.
2. ADS parser: query the [ADS database](https://ui.adsabs.harvard.edu/) to populate information including author list, primary author, authors' affiliations, publication venue, publication date, etc.
3. Paper parser: remove/augment the contents of the parsed text that are general to all papers(e.g., translate some UTF-8 punctuation to ASCII, remove hyphens at the end of lines, etc.).
4. LPSC parser: remove contents specific to the LPSC abstract (e.g., abstract id, abstract header, etc.).
5. CoreNLP parser: named entity recognition. 
6. JSRE parser: relation extraction.

To see the command line arguments for `lpsc_parser.py`, please run the following command:

```
python lpsc_parser.py -h
```

The following command is an example for running `lpsc_parser.py`:

```
python lpsc_parser.py -li /PATH/TO/LIST/OF/PDF/FILES -o /PATH/TO/OUTPUT/JSONL/FILE -l /PATH/TO/OUTPUT/LOG/FILE -n /PATH/TO/TRAINED/NER/MODEL -jr /PATH/TO/TRAINED/JSRE/MODEL
```

**Paper Parser** 

The paper parser is created to process papers from all publicaiton venues. Once the paper parser script is invoked (e.g., calling the `main()` function of the `paper_parser.py` script), the following actions will occur in sequential order to process the input docments to the output jsonl file.


1. TIKA parser: convert the input documents (in PDF format) to text.
2. ADS parser: query the [ADS database](https://ui.adsabs.harvard.edu/) to populate information including author list, primary author, authors' affiliations, publication venue, publication date, etc.
3. Paper parser: remove/augment the contents of the parsed text that are general to all papers(e.g., translate some UTF-8 punctuation to ASCII, remove hyphens at the end of lines, etc.).
4. CoreNLP parser: named entity recognition. 
5. JSRE parser: relation extraction.

To see the command line arguments for `paper_parser.py`, please run the following command:

```
python paper_parser.py -h
```

The following command is an example for running `paper_parser.py`:

```
python paper_parser.py -li /PATH/TO/LIST/OF/PDF/FILES -o /PATH/TO/OUTPUT/JSONL/FILE -l /PATH/TO/OUTPUT/LOG/FILE -n /PATH/TO/TRAINED/NER/MODEL -jr /PATH/TO/TRAINED/JSRE/MODEL
```

**Example use cases**

1. If the documents that we want to process are all from LPSC, then use `lpsc_parser.py`.
2. If the documents that we want to process are from different journals, then use `paper.py`.
