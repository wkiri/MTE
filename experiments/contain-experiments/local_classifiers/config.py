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

