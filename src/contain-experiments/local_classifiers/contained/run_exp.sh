rm -r ./ins
mode=T
python3 make_train_val_test.py --mode $mode

modelSaveDir=./temp/$mode
python3 train.py -mode $mode -train_dir ins/train -val_dir ins/val -test_dir ins/test -lr 0.000005 -epoch 10 -predict_with_extracted_gold_entities 1 -analyze_dev 0 -model_save_dir $modelSaveDir 


mode=EM
python3 make_train_val_test.py --mode $mode
modelSaveDir=./temp/$mode
python3 train.py -mode $mode -train_dir ins/train -val_dir ins/val -test_dir ins/test -lr 0.000005 -epoch 10 -predict_with_extracted_gold_entities 1 -analyze_dev 1 -model_save_dir $modelSaveDir 

rm $modelSaveDir/*.ckpt
rm $modelSaveDir/test/*.ckpt
