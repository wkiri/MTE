# run on mila 
# # # ========== preprocessing, need to run only once ========
mode="Merged" # choices: Element, Mineral, and Merged
addmpfphx=1
usempfphxonly=1
python2 generate_jsre_binary_relation_examples.py --mode $mode --add_mpfphx $addmpfphx --use_mpfphx_only $usempfphxonly # generate jsre examples to trian and predict. modify config.py to make desired experiments. This doesn't include dataset from mpf and phx 


# ========== run experiments ======
mode="Merged"
relation="Contains"
useGoldEntity=1 # 1 or 0, whether use gold entity or system entity to generate test examples 

# ===================================

exampledir="jsre-examples"
traindir=$exampledir"/"$mode"/train"
valdir=$exampledir"/"$mode"/val"
if [ $useGoldEntity = 1 ]
then
	testdir=$exampledir"/"$mode"/test-goldentity"
else
	testdir=$exampledir"/"$mode"/test-sysentity"
fi

cat $traindir/*.examples > $traindir/$mode.train
cat $valdir/*.examples > $valdir/$mode.predict
cat $testdir/*.examples > $testdir/$mode.predict

rm $traindir/$mode.model

if [ "$mode" = "Merged" ] || [ "$t" = "Element" ]
then
	k="LC"
else
	k="SL"
fi

export JSREBASE=/proj/mte/jSRE/jsre-1.1
export CLASSPATH=$JSREBASE/dist/xjsre.jar:`ls $JSREBASE/lib/commons*jar | tr '\012' ':'`:$JSREBASE/lib/libsvm-2.8.jar:$JSREBASE/lib/log4j-1.2.8.jar

# echo "Java classpath is set."

# Check for jSRE config files
if [ ! -e jsre-config.xml ] ; then
    # echo "Copying jsre-config.xml over."
    cp /proj/mte/jSRE/jsre-1.1/jsre-config.xml .
fi
if [ ! -e log-config.txt ] ; then
    # echo "Copying log-config.txt over."
    cp /proj/mte/jSRE/jsre-1.1/log-config.txt .
fi

echo "============ Training jSRE Model ============"
java -mx256M org.itc.irst.tcc.sre.Train -m 256 -k $k -c 5 $traindir/$mode.{train,model}
# java -mx256M org.itc.irst.tcc.sre.Predict $valdir/$mode.predict $traindir/$mode.model $valdir/$mode.output
echo "============ Testing jSRE Model over word-word pair labels ============"
java -mx256M org.itc.irst.tcc.sre.Predict $testdir/$mode.predict $traindir/$mode.model $testdir/$mode.output

echo "========Evaluate Over Entity-Entity Level========"
python2 aggregate_and_eval.py --examples $testdir/$mode.predict --predictions $testdir/$mode.output --evals  $testdir/$mode.std_eval --outfile $testdir/$mode.output.std_entity


