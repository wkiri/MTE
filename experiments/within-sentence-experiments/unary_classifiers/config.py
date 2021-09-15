# python3
# config.py
# Mars Target Encyclopedia
# This script contains experiment settings such as tokenizer type, markers for ners, and label information. 
#
# Yuan Zhuang
# July 30, 2021
# Copyright notice at bottom of file.

# general 
label2ind = {
	"Contains": 0,
	"O": 1,
}
ind2label = { v:k for k, v in label2ind.items()}

tokenizer_type = "bert-base-uncased"

# for span instances
ner2markers = {
	"Element":"E",
	"Mineral":"E",
	"Target":"T"
}

# Copyright 2021, by the California Institute of Technology. ALL
# RIGHTS RESERVED. United States Government Sponsorship
# acknowledged. Any commercial use must be negotiated with the Office
# of Technology Transfer at the California Institute of Technology.
#
# This software may be subject to U.S. export control laws and
# regulations.  By accepting this document, the user agrees to comply
# with all applicable U.S. export laws and regulations.  User has the
# responsibility to obtain export licenses, or other export authority
# as may be required before exporting such information to foreign
# countries or providing access to foreign persons.

