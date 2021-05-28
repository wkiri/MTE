cd /uusoc/exports/scratch/yyzhuang/stanford-corenlp-4.2.0

java -mx60000m -cp "*" edu.stanford.nlp.ie.crf.CRFClassifier  -prop /uusoc/res/nlp/nlp/yuan/mars/experiments/ner.props >& /uusoc/res/nlp/nlp/yuan/mars/saved_models/ner/train_log.txt

# test 
java -cp "*" edu.stanford.nlp.ie.crf.CRFClassifier  -loadClassifier /uusoc/res/nlp/nlp/yuan/mars/saved_models/ner/model.ser.gz -testFile /uusoc/res/nlp/nlp/yuan/mars/data/stanford_ner/test/data.txt  > /uusoc/res/nlp/nlp/yuan/mars/data/stanford_ner/test/data.txt.predicted

# predict 
java -cp "*" edu.stanford.nlp.ie.crf.CRFClassifier  -loadClassifier /uusoc/res/nlp/nlp/yuan/mars/saved_models/ner/model.ser.gz -textFile /uusoc/res/nlp/nlp/yuan/mars/data/corpus-LPSC/lpsc15-C-raymond-sol1159-v3-utf8/1249.txt

# use ner, ssplit,.. again to parse the text file

java -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLP -prop /uusoc/res/nlp/nlp/yuan/mars/experiments/pipeline_with_ner.props -fileList 