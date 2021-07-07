# iaai 
java -mx60000m -cp ".:/proj/mte/modules/stanford-corenlp-custom/*" edu.stanford.nlp.ie.crf.CRFClassifier  -prop train_iaai.props

# test 
java -cp ".:/proj/mte/modules/stanford-corenlp-custom/*" edu.stanford.nlp.ie.crf.CRFClassifier  -loadClassifier /home/yzhuang/MTE/experiments/ner_experiments/corenlp/saved_models/iaai_model.ser.gz -testFile /home/yzhuang/MTE/experiments/ner_experiments/corenlp/iaai-corenlp-setup/35r16v2_new-test.tsv  > saved_model/iaai_test.predicted


# iaai 4.2 
java -mx60000m -cp ".:/proj/mte/stanford-corenlp-mte-4.2.0/*" edu.stanford.nlp.ie.crf.CRFClassifier  -prop train_iaai.props

# test 
java -cp ".:/proj/mte/stanford-corenlp-mte-4.2.0/*" edu.stanford.nlp.ie.crf.CRFClassifier  -loadClassifier /home/yzhuang/MTE/experiments/ner_experiments/corenlp/saved_models/iaai_model.ser.gz -testFile /home/yzhuang/MTE/experiments/ner_experiments/corenlp/iaai-corenlp-setup/35r16v2_new-test.tsv  > saved_model/iaai_test.predicted