# run in mlia 
# make list of files for train dev and test  
# python2 

mkdir data 

find "$(cd ../../../corpus-LPSC/lpsc15-C-raymond-sol1159-v3-utf8; pwd)" -name "*.txt" | sort  > 1.list
find "$(cd ../../../corpus-LPSC/lpsc15-C-raymond-sol1159-v3-utf8; pwd)" -name "*.ann" | sort  > 2.list
paste  -d "," 1.list  2.list  > data/train.list


find "$(cd ../../../corpus-LPSC/lpsc16-C-raymond-sol1159-utf8; pwd)" -name "*.txt" | sort | head -20 > 1.list
find "$(cd ../../../corpus-LPSC/lpsc16-C-raymond-sol1159-utf8; pwd)" -name "*.ann" | sort | head -20 > 2.list
paste  -d "," 1.list  2.list  > data/dev.list

find "$(cd ../../../corpus-LPSC/lpsc16-C-raymond-sol1159-utf8; pwd)" -name "*.txt" | sort | tail -35 > 1.list
find "$(cd ../../../corpus-LPSC/lpsc16-C-raymond-sol1159-utf8; pwd)" -name "*.ann" | sort | tail -35 > 2.list
paste  -d "," 1.list  2.list  > data/test.list

rm 1.list
rm 2.list 
# ==============make input files for ner model 
# need to start a corenlp server at localhost:9000
# do: 
# java -mx4g -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer -port 8000 -timeout 15000

python2 brat2ner_bulkdoc_multiword.py --in data/train.list --out data/train.tsv
python2 brat2ner_bulkdoc_multiword.py --in ./data/dev.list --out ./data/dev.tsv 
python2 brat2ner_bulkdoc_multiword.py --in ./data/test.list --out ./data/test.tsv 

# ========== TRAIN MODEL ========
# train 
mkdir saved_models
# cd ~/stanford-corenlp-4.2.0/
java -mx60000m -cp ".:/proj/mte/stanford-corenlp-mte-4.2.0/*" edu.stanford.nlp.ie.crf.CRFClassifier  -prop train.props

# test 
java -cp ".:/proj/mte/stanford-corenlp-mte-4.2.0/*" edu.stanford.nlp.ie.crf.CRFClassifier  -loadClassifier /home/yzhuang/MTE/experiments/ner_experiments/corenlp/saved_models/model.ser.gz -testFile /home/yzhuang/MTE/experiments/ner_experiments/corenlp/data/test.tsv  > saved_model/test.predicted

# do not need it anymore, since corenlp evalautes over entity level instead of word level 
# python3 make_eval_set.py --testlist  ./data/test.list

# python3 aggregate_predictions.py

# python3 ../eval.py --prediction ./saved_models/test.predicted.entities --gold ./data/test.eval.entities