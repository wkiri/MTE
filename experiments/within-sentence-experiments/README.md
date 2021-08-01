# Introduction
This directory contains experiment codes for within-sentence **(Target, Contains, Component)** relation extraction over MTE dataset. Specifically, it contains codes for the unary classifiers and the relevant model PURE:

+ `PURE/`: 
    It contains the experiment codes to run PURE (modified in order to take the MTE data as input) (https://github.com/princeton-nlp/PURE) over the MTE dataset. For detailed description, check the README file in PURE/.

+ `unary_classifiers/`:
    It contains the experiment codes for within-sentence unary relation extraction (extract "Contains" relations using Containee and Container). For detailed description, check the README file in unary_classifiers/.

+ `unaryParser/`:
    It contains the codes of Unary Parser which performs within-sentence unary relation extraction over unseen texts on the fly.    

---
# Dependencies
Codes in this directory require `python3` and the dependencies listed in `requirement.txt`. To set up the dependencies, do the following:

    pip install -r requirement.txt

---
# Data Preparation
Experiments in both PURE/ and unary_classifiers/ need CoreNLP to parse the text files from the collection of MSL, MPF and PHX first, while unaryParser/ doesn't need it. If you do want to run experiments in PURE/ and unary_classifiers/, you'll need to:

+ First install StanfordCoreNLP-4.2.0 by following the instruction at https://stanfordnlp.github.io/CoreNLP/. 

+ Once StanfordCoreNLP is installed, run the following script to parse text files from MSL, MPF and PHX. Parsing results would then be saved at ../../parse/:
    
    ```
    python3 parse_texts.py \
    --indir \
        ../../corpus-LPSC/lpsc15-C-raymond-sol1159-v3-utf8 \
        ../../corpus-LPSC/lpsc16-C-raymond-sol1159-utf8/ \
        ../../corpus-LPSC/mpf-reviewed+properties-v2/ \
        ../../corpus-LPSC/phx-reviewed+properties-v2 \
    --outdir ../../parse1 \
    --corenlp_dir <PATH/TO/stanford-corenlp-4.2.0>
    ```
---
# Running Experiments

As dependencies and data preparation are done, you could move into PURE/, unary_classifiers/ and unaryParser/, and run experiments by following the instructions in the README file there.
