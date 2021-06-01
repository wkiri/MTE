declare -a venues=("lpsc16-C-raymond-sol1159-utf8" "mpf-reviewed+properties-v2" "phx-reviewed+properties-v2")

# run pure 
cd PURE
python make_train_dev_test.py --test_venues "${venues[@]}" --use_component 

# train pure 
export CUDA_VISIBLE_DEVICES=1;
python run_relation.py \
  --task mars\
  --do_train \
  --do_eval --eval_with_gold \
  --train_file train/docs.json \
  --val_file dev/docs.json \
  --model bert-base-uncased \
  --do_lower_case \
  --train_batch_size 10 \
  --eval_batch_size 32 \
  --learning_rate 2e-5 \
  --num_train_epochs 10 \
  --context_window 0	\
  --max_seq_length 512 	\
  --output_dir ./temp/rel
  # --entity_output_dir {path to output files of the entity model} \

# make predictions for test set 
export CUDA_VISIBLE_DEVICES=1;
python run_relation.py \
  --task mars\
  --do_eval --eval_test --eval_with_gold \
  --test_file test/docs.json \
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
python match_purepred_to_instance.py 

# evaluate the predictions over gold testset 
python ../eval.py --pred_relins ./temp/rel/predictions.pkl --gold_relins ./test/gold_relins.pkl

cd ..

# develop container
cd contained
mode=EM
python3 make_train_dev_test.py --mode $mode --test_venues "${venues[@]}"

modelSaveDir=./temp/$mode
python3 train.py -mode $mode -train_dir ins/train -val_dir ins/dev -test_dir ins/test -lr 0.000005 -epoch 10 -predict_with_extracted_gold_entities 1 -analyze_dev 0 -model_save_dir $modelSaveDir 

cd .. 
# combine predictions 
cd combine_prediction

python pipeline.py -spans ../contained/temp/$mode/test/$mode.spans.pred -rels ../PURE/temp/rel/predictions.pkl -gold_rels ../PURE/test/gold_relins.pkl -boost_precision 1 -boost_recall 0






