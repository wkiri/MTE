
mode=EM
useGoldEntities=1
# contained experiments
python3 contained/make_train_val_test.py --mode $mode
modelSaveDir=./contained/temp
traindir=./contained/ins/train
valdir=./contained/ins/val
testdir=./contained/ins/test


python3 contained/train.py -mode $mode -train_dir $traindir -val_dir $valdir -test_dir $testdir -lr 0.000005 -epoch 10 -predict_with_extracted_gold_entities $useGoldEntities -analyze_dev 0 -model_save_dir $modelSaveDir 

rm $modelSaveDir/*.ckpt
rm $modelSaveDir/test/*.ckpt

# relation model experiments
python3 relation_model/make_train_val_test.py -mode $mode

traindir=./relation_model/rels/train
valdir=./relation_model/rels/val
testdir=./relation_model/rels/test
modelSaveDir=./relation_model/temp

python relation_model/train.py -mode $mode -train_dir $traindir -val_dir $valdir -test_dir $testdir -lr 0.00001 -epoch 20 -predict_with_extracted_gold_entities $useGoldEntities -analyze_dev 0 -model_save_dir $modelSaveDir 

rm $modelSaveDir/*.ckpt
rm $modelSaveDir/test/*.ckpt
# ===== combine 
boostP=1
boostR=1
python combine_prediction/pipeline.py -spans contained/temp/test/$mode.spans.pred -rels relation_model/temp/test/$mode.rels.pred -gold_rels relation_model/rels/test/$mode.annotated_gold_relins.pkl -boost_precision $boostP -boost_recall $boostR
