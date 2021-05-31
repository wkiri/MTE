addmpfphx=1
usempfphxonly=0
rm -r rels
mode=EM

python3 make_train_val_test.py -mode $mode -use_mpfphx_only $usempfphxonly -add_mpfphx $addmpfphx

modelSaveDir=./temp/$mode
python train.py -mode $mode -train_dir rels/train -val_dir rels/val -test_dir rels/test -lr 0.00001 -epoch 20 -predict_with_extracted_gold_entities 1 -analyze_dev 1 -model_save_dir $modelSaveDir 
