useSysNers=0
pred_threshold=0.5

make_data_for_containee=1
doTrainContainee=1
eval_containee_dev=1
eval_containee_test=1

export CUDA_VISIBLE_DEVICES=1;
declare -a venues=( "lpsc16-C-raymond-sol1159-utf8" "mpf-reviewed+properties-v2" "phx-reviewed+properties-v2"
  )


if [ "$make_data_for_containee" = "1" ]
then
  python3 make_train_dev_test.py  --test_venues "${venues[@]}" 
fi

modelSaveDir=./temp/
if [ "$doTrainContainee" = "1" ]
then
python3 train.py  -train_dir ins/train -val_dir ins/dev/gold_ner  -lr 0.00001 -epoch 10  -analyze_dev 1 -model_save_dir $modelSaveDir
fi


if [ "$eval_containee_dev" = "1" ]
then
	if [ "$useSysNers" = "1" ]
	then
		testdir=ins/dev/sys_ner
	else
		testdir=ins/dev/gold_ner
	fi
	python3 predict.py -modelfile "$modelSaveDir/trained_model.ckpt" -test_dir $testdir -analyze_dev 0 -outdir $modelSaveDir -threshold $pred_threshold
fi 

if [ "$eval_containee_test" = "1" ]
	if [ "$useSysNers" = "1" ]
	then
		testdir=ins/test/sys_ner
	else
		testdir=ins/test/gold_ner
	fi
then
python3 predict.py -modelfile "$modelSaveDir/trained_model.ckpt" -test_dir $testdir -analyze_dev 0 -outdir $modelSaveDir -threshold $pred_threshold
fi

