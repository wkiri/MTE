useComponent=1
useSysNers=1
make_data_for_pure=0
doTrainPURE=0
eval_pure_dev=0
eval_pure_test=1

export CUDA_VISIBLE_DEVICES=1;
declare -a venues=( "lpsc16-C-raymond-sol1159-utf8" "mpf-reviewed+properties-v2" "phx-reviewed+properties-v2"
  )

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
    --val_file ./data/dev/gold_ner/docs.json \
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
  if [ "$useSysNers" = "1" ]
  then
    testfile=./data/dev/sys_ner/docs.json
  else 
    testfile=./data/dev/gold_ner/docs.json
  fi
  python run_relation.py \
  --task mars\
  --do_eval --eval_test --eval_with_gold \
  --test_file $testfile \
  --model bert-base-uncased \
  --do_lower_case \
  --eval_batch_size 10 \
  --context_window 0  \
  --max_seq_length 512  \
  --output_dir ./temp/rel \
  --add_new_tokens
  # match predictions from PURE back to instance
  python match_purepred_to_instance.py --use_component $useComponent --pred_file ./temp/rel/predictions.json
  # evaluate the predictions over gold testset 
  python ../eval.py --pred_relins ./temp/rel/predictions.pkl --gold_relins ./data/dev/gold_relins.pkl --analyze 1
fi 

if [ "$eval_pure_test" = 1 ]
  
then
  if [ "$useSysNers" = "1" ]
  then
    testfile=./data/test/sys_ner/docs.json
  else 
    testfile=./data/test/gold_ner/docs.json
  fi
  python run_relation.py \
  --task mars\
  --do_eval --eval_test --eval_with_gold \
  --test_file $testfile \
  --model bert-base-uncased \
  --do_lower_case \
  --eval_batch_size 10 \
  --context_window 0  \
  --max_seq_length 512  \
  --output_dir ./temp/rel
  # match predictions from PURE back to instance
  python match_purepred_to_instance.py --use_component $useComponent
  # evaluate the predictions over gold testset 
  python ../eval.py --pred_relins ./temp/rel/predictions.pkl --gold_relins ./data/test/gold_relins.pkl --analyze 0
fi

