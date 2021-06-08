useComponent=1
make_data_for_pure=0
doTrainPURE=0
eval_pure_dev=1
eval_pure_test=0

make_data_for_containee=0
doTrainContainee=0
eval_containee_dev=1
eval_containee_test=1

pred_threshold=0.5

combine_dev=1
combine_test=0
export CUDA_VISIBLE_DEVICES=1;
declare -a venues=( "lpsc16-C-raymond-sol1159-utf8" "mpf-reviewed+properties-v2" "phx-reviewed+properties-v2"
  )


# run pure 
cd PURE
if [ "$make_data_for_pure" = "1" ]
then
  python make_train_dev_test.py --test_venues "${venues[@]}" --use_component $useComponent
fi

if [  "$doTrainPURE" = "1" ]
then
  # train PURE
  python run_relation.py \
    --task mars\
    --do_train \
    --do_eval --eval_with_gold \
    --train_file ./data/train/docs.json \
    --val_file ./data/dev/docs.json \
    --model bert-base-uncased \
    --do_lower_case \
    --train_batch_size 10 \
    --eval_batch_size 10 \
    --learning_rate 0.0001 \
    --num_train_epochs 30 \
    --context_window 0	\
    --max_seq_length 512 	\
    --output_dir ./temp/rel/ \
    --eval_per_epoch 1 \
    --add_new_tokens
fi 


if [ "$eval_pure_dev" = "1" ]
then 
  python run_relation.py \
  --task mars\
  --do_eval --eval_test --eval_with_gold \
  --test_file ./data/dev/docs.json \
  --model bert-base-uncased \
  --do_lower_case \
  --eval_batch_size 10 \
  --context_window 0  \
  --max_seq_length 512  \
  --output_dir ./temp/rel \
  --add_new_tokens
  # match predictions from PURE back to instance
  python match_purepred_to_instance.py --use_component $useComponent
  # evaluate the predictions over gold testset 
  python ../eval.py --pred_relins ./temp/rel/predictions.pkl --gold_relins ./data/dev/gold_relins.pkl --analyze 1
fi 

if [ "$eval_pure_test" = 1 ]
then
  python run_relation.py \
  --task mars\
  --do_eval --eval_test --eval_with_gold \
  --test_file ./data/test/docs.json \
  --model bert-base-uncased \
  --do_lower_case \
  --train_batch_size 32 \
  --eval_batch_size 10 \
  --learning_rate 2e-5 \
  --num_train_epochs 10 \
  --context_window 0  \
  --max_seq_length 512  \
  --output_dir ./temp/rel
  # match predictions from PURE back to instance
  python match_purepred_to_instance.py --use_component $useComponent
  # evaluate the predictions over gold testset 
  python ../eval.py --pred_relins ./temp/rel/predictions.pkl --gold_relins ./data/test/gold_relins.pkl --analyze 1
fi

cd ..


# develop container
cd contained
content=EM
if [ "$make_data_for_containee" = "1" ]
then
  python3 make_train_dev_test.py --content $content --test_venues "${venues[@]}" 
fi

modelSaveDir=./temp/$content
if [ "$doTrainContainee" = "1" ]
then
python3 train.py -content $content -train_dir ins/train -val_dir ins/dev  -lr 0.00001 -epoch 10 -predict_with_extracted_gold_entities 1 -analyze_dev 1 -model_save_dir $modelSaveDir
fi

if [ "$eval_containee_dev" = "1" ]
then
python3 predict.py -content $content -modelfile "$modelSaveDir/trained_model.ckpt" -test_dir ins/dev -predict_with_extracted_gold_entities 1 -analyze_dev 0 -outdir $modelSaveDir -threshold $pred_threshold
fi 

if [ "$eval_containee_test" = "1" ]
then
python3 predict.py -content $content -modelfile "$modelSaveDir/trained_model.ckpt" -test_dir ins/test -predict_with_extracted_gold_entities 1 -analyze_dev 0 -outdir $modelSaveDir -threshold $pred_threshold
fi

cd .. 
# combine predictions 
cd combine_prediction
if [  "$combine_dev" = "1" ]
then
python pipeline.py -spans ../contained/temp/$content/$content.spans.pred -rels ../PURE/temp/rel/predictions.pkl -gold_rels ../PURE/data/dev/gold_relins.pkl -boost_precision 0 -boost_recall 1
fi 

if [  "$combine_test" = "1" ]
then
python pipeline.py -spans ../contained/temp/$content/$content.spans.pred -rels ../PURE/temp/rel/predictions.pkl -gold_rels ../PURE/data/test/gold_relins.pkl -boost_precision 0 -boost_recall 1
fi 

cd ..




