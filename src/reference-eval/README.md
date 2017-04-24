# Reference Extractor Evaluation
- [Ground Truth](ground-truth)
Each file in this directory contains a list of references, **manually extracted**, from the respective journal abstract and is named after the abstract id.
- [Extracted](extracted)
Each file in this directory contains a list of references, **extracted by reference-extractor**, from the respective journal abstract and is named after the abstract id.
- evaluate-referenceparser.py
Evaluates the reference extractor by comparing the extracted references with that of ground truth.
usage: evaluate_referenceparser.py [-h] [-gt GROUNDTRUTH] [-ex EXTRACTED]
where 'GROUNDTRUTH' and 'EXTRACTED' are the path to their respective directories
