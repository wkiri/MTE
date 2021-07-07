#!/bin/bash
# this code reproduces Table 4 in the IAAI 2018 paper. NOTE that this evalutes over the set of relations both of which system entities are predicted correctly by the NER model. As a result, it doesn't evaluate over relations of which at least one argument entity is not recognized as element/mineral/target by the NER model .   

# This bash code requires lpsc15-utf8 and lpsc16-utf8 exist first. Generating this two folders follows jsre_labeling_corenlp_and_brat.py

# example command line: 
# 	bash run_exp_iaai.sh element

# ============ TO MODIFY ======
t=$1 # indicate what experiment should be run. mineral, element or merged. choices: mineral, element, merged

# =============== DO NOT MODIFY ==========

# Set up for jSRE experiments
# Set the Java CLASSPATH
export JSREBASE=/proj/mte/jSRE/jsre-1.1
export CLASSPATH=$JSREBASE/dist/xjsre.jar:`ls $JSREBASE/lib/commons*jar | tr '\012' ':'`:$JSREBASE/lib/libsvm-2.8.jar:$JSREBASE/lib/log4j-1.2.8.jar

echo "Java classpath is set."

# Check for jSRE config files
if [ ! -e jsre-config.xml ] ; then
    echo "Copying jsre-config.xml over."
    cp /proj/mte/jSRE/jsre-1.1/jsre-config.xml .
fi
if [ ! -e log-config.txt ] ; then
    echo "Copying log-config.txt over."
    cp /proj/mte/jSRE/jsre-1.1/log-config.txt .
fi

# =====================================
mkdir ./iaai
traindir="iaai/train-"$t
valdir="iaai/val-"$t
testdir="iaai/test-"$t
mkdir $traindir; mkdir $valdir; mkdir $testdir

if [ "$t" = "merged" ]
then
	find lpsc15-utf8/*-element.examples -maxdepth 1 -type f | sort -z | head -42|xargs cp -t $traindir
	find lpsc15-utf8/*-mineral.examples -maxdepth 1 -type f | sort -z | head -42|xargs cp -t $traindir
	find lpsc15-utf8/*-element.examples -maxdepth 1 -type f | sort -z | tail -20|xargs cp -t $valdir
	find lpsc15-utf8/*-mineral.examples -maxdepth 1 -type f | sort -z | tail -20|xargs  cp -t $valdir

	cp lpsc16-utf8/*-element.examples $testdir
	cp lpsc16-utf8/*-mineral.examples $testdir


else
	find lpsc15-utf8/*-$t.examples -maxdepth 1 -type f | sort -z | head -42|xargs cp -t $traindir
	find lpsc15-utf8/*-$t.examples -maxdepth 1 -type f | sort -z | tail -21|xargs  cp -t $valdir

	cp lpsc16-utf8/*-$t.examples $testdir
fi

cat $traindir/*.examples > $traindir/$t.train
cat $valdir/*.examples > $valdir/$t.predict
cat $testdir/*.examples > $testdir/$t.predict

# convert labels to binary 
python convert_label_iaai.py $traindir/$t.train $traindir/$t.train
python convert_label_iaai.py $valdir/$t.predict $valdir/$t.predict
python convert_label_iaai.py $testdir/$t.predict $testdir/$t.predict

rm $traindir/$t.model

if [ "$t" = "merged" ] || [ "$t" = "element" ]
then
	# NOTICE that -c here is not window size.  Instead it is svm-cost.
	k="LC"
else
	k="SL"
fi

java -mx256M org.itc.irst.tcc.sre.Train -m 256 -k $k -c 5 $traindir/$t.{train,model}
java -mx256M org.itc.irst.tcc.sre.Predict $valdir/$t.predict $traindir/$t.model $valdir/$t.output
java -mx256M org.itc.irst.tcc.sre.Predict $testdir/$t.predict $traindir/$t.model $testdir/$t.output

