#!/bin/csh

#This csh script takes train.list and test.list in the format described in 
#the step 4 of the URL below as inputs, and then creates a Stanford CoreNLP  
#NER model, and the statistcs of testing will be captured in log file.
#  
#https://github.com/USCDataScience/parser-indexer-py/tree/master/src/corenlp
#
#USAGE:
#./train_corenlp_ner.csh train.list test.list [outdir]
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

# Use the specified output directory, or fall back on current directory
if ( $# == 3 ) then
    set outdir = $3
    echo changing outdir to $outdir
else
    set outdir = $PWD
endif
echo Writing output files to $outdir

set train_list = $1
set test_list = $2
set train_name = `basename $train_list`
set test_name  = `basename $test_list`
set train_tokens = ($train_name:as/./ /)
set test_tokens  = ($test_name:as/./ /)
set train_name = $outdir/$train_tokens[1]
set test_name  = $outdir/$test_tokens[1]
set lpsc_prop_file = $outdir/lpsc_$train_tokens[1].prop
set lpsc_train_log = $outdir/lpsc_$train_tokens[1].train_log
set lpsc_test_log  = $outdir/lpsc_$train_tokens[1].test_log
set ner_model_file = $outdir/ner_model_$train_tokens[1].ser.gz

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
if (-f $lpsc_prop_file) then
    rm $lpsc_prop_file
endif

if (-f $ner_model_file) then 
    rm $ner_model_file
endif

echo "trainFile = ${train_name}.tsv" > $lpsc_prop_file
echo "serializeTo = $ner_model_file" >> $lpsc_prop_file
echo "map = word=0,answer=1" >> $lpsc_prop_file 
#echo "qnSize=25" >> $lpsc_prop_file
#echo "saveFeatureIndexToDisk=true" >> $lpsc_prop_file
echo "printFeatures=true" >> $lpsc_prop_file
echo "useClassFeature=true" >> $lpsc_prop_file
echo "useWord=true" >> $lpsc_prop_file
echo "useNGrams=true" >> $lpsc_prop_file
echo "noMidNGrams=true" >> $lpsc_prop_file
echo "useDisjunctive=true" >> $lpsc_prop_file
echo "maxNGramLeng=6" >> $lpsc_prop_file
echo "usePrev=true" >> $lpsc_prop_file
echo "useNext=true" >> $lpsc_prop_file
echo "useSequences=true" >> $lpsc_prop_file
echo "usePrevSequences=true" >> $lpsc_prop_file
echo "maxLeft=1" >> $lpsc_prop_file
echo "useTypeSeqs=true" >> $lpsc_prop_file
echo "useTypeSeqs2=true" >> $lpsc_prop_file
echo "useTypeySequences=true" >> $lpsc_prop_file
echo "wordShape=chris2useLC" >> $lpsc_prop_file
echo "cleanGazette=true" >> $lpsc_prop_file
#echo "gazette=targets_minerals-2017-05_elements.gaz.txt" >> $lpsc_prop_file
echo "gazette=targets_minerals_elements-2019-04-sol2224.gaz.txt" >> $lpsc_prop_file

#training
if (-f $lpsc_train_log) then
    rm $lpsc_train_log
endif

set start_fmt = `date +%s`
set start = `date`
#java -Xmx60000m -cp ".:/proj/mte/modules/stanford-corenlp-custom/*" edu.stanford.nlp.ie.crf.CRFClassifier  -prop $lpsc_prop_file >& $lpsc_train_log
java -mx60000m -cp ".:/proj/mte/modules/stanford-corenlp-custom/*" edu.stanford.nlp.ie.crf.CRFClassifier  -prop $lpsc_prop_file >& $lpsc_train_log
#java -mx60000m -cp ".:/proj/mte/modules/stanford-corenlp-custom/*" edu.stanford.nlp.ie.crf.CRFClassifier  -prop $lpsc_prop_file 
set end_fmt = `date +%s`
set end = `date`
@ run = $end_fmt - $start_fmt
echo "start time: $start | ${start_fmt}s" >> $lpsc_train_log
echo "end time: $end | ${end_fmt}s" >> $lpsc_train_log
echo "total run time: ${run}s" >> $lpsc_train_log

#testing
if (-f $lpsc_test_log) then
    rm $lpsc_test_log
endif
set start_fmt = `date +%s`
set start = `date`
java -cp ".:/proj/mte/modules/stanford-corenlp-custom/*" edu.stanford.nlp.ie.crf.CRFClassifier  -loadClassifier $ner_model_file -testFile ${test_name}.tsv >& $lpsc_test_log
#java -cp ".:/proj/mte/modules/stanford-corenlp-custom/*" edu.stanford.nlp.ie.crf.CRFClassifier  -loadClassifier $ner_model_file -testFile ${test_name}.tsv 
set end_fmt = `date +%s`
set end = `date`
@ run = $end_fmt - $start_fmt
echo "start time: $start | ${start_fmt}s" >> $lpsc_test_log
echo "end time: $end | ${end_fmt}s" >> $lpsc_test_log
echo "total run time: ${run}s" >> $lpsc_test_log

#send email notification
if (-f email.txt) then
    rm email.txt
endif

echo "Train list: ${train_name}.list" > email.txt
echo "Train log: ${train_name}.log" >> email.txt
echo "Test list: ${test_name}.list" >> email.txt
echo "Test log: ${test_name}.log" >> email.txt
echo "NER model: $lpsc_prop_file" >> email.txt
echo "Training log: $lpsc_train_log" >> email.txt
echo "Testing log: $lpsc_test_log" >> email.txt

echo `cat email.txt` | mail -s "training and testing for ${train_name}.list complete" wkiri@jpl.nasa.gov
