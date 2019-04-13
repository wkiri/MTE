#!/bin/csh

#This csh script takes train.list and test.list in the format described in 
#the step 4 of the URL below as inputs, and then creates a Stanford CoreNLP  
#NER model, and the statistcs of testing will be captured in log file.
#  
#https://github.com/USCDataScience/parser-indexer-py/tree/master/src/corenlp
#
#USAGE:
#./train_corenlp_ner.csh train.list test.list
#
#OUTPUT:
#1. train.log -- it captures the messages for converting train.list 
#                to train.tsv. Elapsed time is included at the end.
#2. test.log -- it captures the messages for converting test.list to
#               test.tsv. Elapsed time is included at the end.
#3. lpsc_train.prop -- Stanford CoreNLP training properties file.
#4. lpsc_train.train_log -- it captures the messages for training.
#                            Elapsed time is included at the end.              
#5. lpsc_train.test_log -- it captures the messages for testing. 
#                          Testing statistics such as precision 
#                          and recall are logged as well. 
#NOTE:
#A email notification will be sent once all the processes are completed.
#If you would like to receive those emails, add your email address at 
#the bottom of the script.

set train_list = $1
set test_list = $2
set train_tokens = ($train_list:as/./ /)
set test_tokens = ($test_list:as/./ /)
set train_name = $train_tokens[1]
set test_name = $test_tokens[1]

if (-f ${test_name}.tsv) then
    goto convert_training
else
    if (-f ${test_name}.log) then
        rm ${test_name}.log
    endif

    #convert test list from brat to ner
    set start_fmt = `date +%s`
    set start = `date`
    python brat2ner_bulkdoc_multiword.py --in ${test_name}.list --out ${test_name}.tsv > ${test_name}.log
    #python /proj/mte/modules/parser-indexer-py/src/corenlp/brat2ner_bulkdoc_multiword.py --in ${test_name}.list --out ${test_name}.tsv > ${test_name}.log
    #python /proj/mte/modules/parser-indexer-py/src/corenlp/brat2ner_bulkdoc_multiword.py --in ${test_name}.list --out ${test_name}.tsv 
    set end_fmt = `date +%s`
    set end = `date`
    @ run = $end_fmt - $start_fmt
    echo "start time: $start | ${start_fmt}s" >> ${test_name}.log
    echo "end time: $end | ${end_fmt}s" >> ${test_name}.log
    echo "total run time: ${run}s" >> ${test_name}.log
endif

convert_training:
#convert train list from brat to ner
if (-f ${train_name}.log) then
    rm ${train_name}.log
endif
set start_fmt = `date +%s`
set start = `date`
python brat2ner_bulkdoc_multiword.py --in ${train_name}.list --out ${train_name}.tsv > ${train_name}.log
#python /proj/mte/modules/parser-indexer-py/src/corenlp/brat2ner_bulkdoc_multiword.py --in ${train_name}.list --out ${train_name}.tsv > ${train_name}.log
#python /proj/mte/modules/parser-indexer-py/src/corenlp/brat2ner_bulkdoc_multiword.py --in ${train_name}.list --out ${train_name}.tsv
set end_fmt = `date +%s`
set end = `date`
@ run = $end_fmt - $start_fmt
echo "start time: $start | ${start_fmt}s" >> ${train_name}.log
echo "end time: $end | ${end_fmt}s" >> ${train_name}.log
echo "total run time: ${run}s" >> ${train_name}.log
#generate properties file
if (-f lpsc_${train_name}.prop) then
    rm lpsc_${train_name}.prop
endif

if (-f ner_model_${train_name}.ser.gz) then 
    rm ner_model_${train_name}.ser.gz
endif

echo "trainFile = ${train_name}.tsv" > lpsc_${train_name}.prop
echo "serializeTo = ner_model_${train_name}.ser.gz" >> lpsc_${train_name}.prop
echo "map = word=0,answer=1" >> lpsc_${train_name}.prop 
#echo "qnSize=25" >> lpsc_${train_name}.prop
#echo "saveFeatureIndexToDisk=true" >> lpsc_${train_name}.prop
echo "printFeatures=true" >> lpsc_${train_name}.prop
echo "useClassFeature=true" >> lpsc_${train_name}.prop
echo "useWord=true" >> lpsc_${train_name}.prop
echo "useNGrams=true" >> lpsc_${train_name}.prop
echo "noMidNGrams=true" >> lpsc_${train_name}.prop
echo "useDisjunctive=true" >> lpsc_${train_name}.prop
echo "maxNGramLeng=6" >> lpsc_${train_name}.prop
echo "usePrev=true" >> lpsc_${train_name}.prop
echo "useNext=true" >> lpsc_${train_name}.prop
echo "useSequences=true" >> lpsc_${train_name}.prop
echo "usePrevSequences=true" >> lpsc_${train_name}.prop
echo "maxLeft=1" >> lpsc_${train_name}.prop
echo "useTypeSeqs=true" >> lpsc_${train_name}.prop
echo "useTypeSeqs2=true" >> lpsc_${train_name}.prop
echo "useTypeySequences=true" >> lpsc_${train_name}.prop
echo "wordShape=chris2useLC" >> lpsc_${train_name}.prop
echo "cleanGazette=true" >> lpsc_${train_name}.prop
echo "gazette=targets_minerals-2017-05_elements.gaz.txt" >> lpsc_${train_name}.prop

#training
if (-f lpsc_${train_name}.train_log) then
    rm lpsc_${train_name}.train_log
endif

set start_fmt = `date +%s`
set start = `date`
#java -Xmx60000m -cp ".:/proj/mte/modules/stanford-corenlp-custom/*" edu.stanford.nlp.ie.crf.CRFClassifier  -prop lpsc_${train_name}.prop >& lpsc_${train_name}.train_log
java -mx60000m -cp ".:/proj/mte/modules/stanford-corenlp-custom/*" edu.stanford.nlp.ie.crf.CRFClassifier  -prop lpsc_${train_name}.prop >& lpsc_${train_name}.train_log
#java -mx60000m -cp ".:/proj/mte/modules/stanford-corenlp-custom/*" edu.stanford.nlp.ie.crf.CRFClassifier  -prop lpsc_${train_name}.prop 
set end_fmt = `date +%s`
set end = `date`
@ run = $end_fmt - $start_fmt
echo "start time: $start | ${start_fmt}s" >> lpsc_${train_name}.train_log
echo "end time: $end | ${end_fmt}s" >> lpsc_${train_name}.train_log
echo "total run time: ${run}s" >> lpsc_${train_name}.train_log

#testing
if (-f lpsc_${train_name}.test_log) then
    rm lpsc_${train_name}.test_log
endif
set start_fmt = `date +%s`
set start = `date`
java -cp ".:/proj/mte/modules/stanford-corenlp-custom/*" edu.stanford.nlp.ie.crf.CRFClassifier  -loadClassifier ner_model_${train_name}.ser.gz -testFile ${test_name}.tsv >& lpsc_${train_name}.test_log
#java -cp ".:/proj/mte/modules/stanford-corenlp-custom/*" edu.stanford.nlp.ie.crf.CRFClassifier  -loadClassifier ner_model_${train_name}.ser.gz -testFile ${test_name}.tsv 
set end_fmt = `date +%s`
set end = `date`
@ run = $end_fmt - $start_fmt
echo "start time: $start | ${start_fmt}s" >> lpsc_${train_name}.test_log
echo "end time: $end | ${end_fmt}s" >> lpsc_${train_name}.test_log
echo "total run time: ${run}s" >> lpsc_${train_name}.test_log

#send email notification
if (-f email.txt) then
    rm email.txt
endif

echo "Train list: $PWD/${train_name}.list" > email.txt
echo "Train log: $PWD/${train_name}.log" >> email.txt
echo "Test list: $PWD/${test_name}.list" >> email.txt
echo "Test log: $PWD/${test_name}.log" >> email.txt
echo "NER model: $PWD/lpsc_${train_name}.prop" >> email.txt
echo "Training log: $PWD/lpsc_${train_name}.train_log" >> email.txt
echo "Testing log: $PWD/lpsc_${train_name}.test_log" >> email.txt

echo `cat email.txt` | mail -s "training and testing for ${train_name}.list complete" wkiri@jpl.nasa.gov
