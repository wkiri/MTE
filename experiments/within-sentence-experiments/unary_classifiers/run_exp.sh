export CUDA_VISIBLE_DEVICES=1;
# declare -a venues=( "lpsc16-C-raymond-sol1159-utf8" "mpf-reviewed+properties-v2" "phx-reviewed+properties-v2"
  )

declare -a venues=( "mpf-reviewed+properties-v2" "phx-reviewed+properties-v2"
  )
useComponent=1
useSysNers=0
# ========PURE=========
make_data_for_pure=1
doTrainPURE=0
eval_pure_dev=0
eval_pure_test=1
# =======CONTAINEE=====
make_data_for_containee=1
doTrainContainee=0
eval_containee_dev=0
eval_containee_test=1
pred_threshold=0.5
# =======CONTAINER=====
make_data_for_container=1
doTrainContainer=0
eval_container_dev=0
eval_container_test=1
pred_threshold=0.5
# =======Combine=======
combine_dev=1
combine_test=0
boost_recall=1
boost_precision=1



# ===============PURE===============

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
    --context_window 0  \
    --max_seq_length 512  \
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
  output_dir=./temp/rel
  python run_relation.py \
  --task mars\
  --do_eval --eval_test --eval_with_gold \
  --test_file $testfile \
  --model bert-base-uncased \
  --do_lower_case \
  --eval_batch_size 10 \
  --context_window 0  \
  --max_seq_length 512  \
  --output_dir $output_dir \
  --add_new_tokens
  # match predictions from PURE back to instance
  python match_purepred_to_instance.py --use_component $useComponent --pred_file $output_dir/predictions.json
  mkdir $output_dir/dev
  mv $output_dir/predictions.pkl $output_dir/dev/predictions.pkl
  # evaluate the predictions over gold testset 
  python ../eval.py --pred_relins $output_dir/dev/predictions.pkl --gold_relins ./data/dev/gold_relins.pkl --analyze 1

  # ======= ALL YES BASELINE ====
  # python ../eval.py --pred_relins ./temp/rel/predictions.pkl --gold_relins ./data/test/gold_relins.pkl --analyze 1 --use_all_yes 1
fi 

if [ "$eval_pure_test" = 1 ]
then
  if [ "$useSysNers" = "1" ]
  then
    testfile=./data/test/sys_ner/docs.json
  else 
    testfile=./data/test/gold_ner/docs.json
  fi
  output_dir=./temp/rel
  python run_relation.py \
  --task mars\
  --do_eval --eval_test --eval_with_gold \
  --test_file $testfile \
  --model bert-base-uncased \
  --do_lower_case \
  --eval_batch_size 10 \
  --context_window 0  \
  --max_seq_length 512  \
  --output_dir $output_dir 
  # match predictions from PURE back to instance
  python match_purepred_to_instance.py --use_component $useComponent --pred_file $output_dir/predictions.json
  mkdir $output_dir/test
  mv $output_dir/predictions.pkl $output_dir/test/predictions.pkl
  # evaluate the predictions over gold testset 
  python ../eval.py --pred_relins $output_dir/test/predictions.pkl --gold_relins ./data/test/gold_relins.pkl --analyze 0

  # # =========== ALL YES BASELINE ====

  # python ../eval.py --pred_relins ./temp/rel/predictions.pkl --gold_relins ./data/test/gold_relins.pkl --analyze 1 --use_all_yes 1
fi



cd ../containee
# USING PURE/ENV3!!!
# ==============CONTAINEE============
# develop containee
if [ "$make_data_for_containee" = "1" ]
then
  python3 make_train_dev_test.py  --test_venues "${venues[@]}" 
fi

modelSaveDir=./temp
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
  mkdir $modelSaveDir/dev
  python3 predict.py -modelfile "$modelSaveDir/trained_model.ckpt" -test_dir $testdir -analyze_dev 0 -outdir $modelSaveDir/dev -threshold 0.5
fi 

if [ "$eval_containee_test" = "1" ]
  if [ "$useSysNers" = "1" ]
  then
    testdir=ins/test/sys_ner
  else
    testdir=ins/test/gold_ner
  fi
then
mkdir $modelSaveDir/test
python3 predict.py -modelfile "$modelSaveDir/trained_model.ckpt" -test_dir $testdir -analyze_dev 0 -outdir $modelSaveDir/test -threshold 0.5
fi

# # ============CONTAINER============
cd ../container
if [ "$make_data_for_container" = "1" ]
then
  python3 make_train_dev_test.py --test_venues "${venues[@]}" 
fi

modelSaveDir=./temp
if [ "$doTrainContainer" = "1" ]
then
python3 train.py -train_dir ins/train -val_dir ins/dev  -lr 0.000005 -epoch 10 -predict_with_extracted_gold_entities 1 -analyze_dev 1 -model_save_dir $modelSaveDir
fi


if [ "$eval_container_dev" = "1" ]
then
mkdir $modelSaveDir/dev
python3 predict.py  -modelfile "$modelSaveDir/trained_model.ckpt" -test_dir ins/dev -predict_with_extracted_gold_entities 1 -analyze_dev 0 -outdir $modelSaveDir/dev -threshold 0.5
fi 

if [ "$eval_container_test" = "1" ]
then
mkdir $modelSaveDir/test
python3 predict.py  -modelfile "$modelSaveDir/trained_model.ckpt" -test_dir ins/test -predict_with_extracted_gold_entities 1 -analyze_dev 0 -outdir $modelSaveDir/test -threshold 0.5
fi
# # ===========COMBINED PREDICTION with Containee AND PURE ================
# cd .. 
# # combine predictions 
# cd combine_prediction
# if [ "$combine_dev" = "1" ]
# then
#   python containee_pipeline.py -spans ../containee/temp/dev/spans.pred -rels ../PURE/temp/rel/dev/predictions.pkl -gold_rels ../PURE/data/dev/gold_relins.pkl -boost_precision $boost_precision -boost_recall $boost_recall 
# fi

# if [ "$combine_test" = "1" ]
# then
#   python containee_pipeline.py -spans ../containee/temp/test/spans.pred -rels ../PURE/temp/rel/test/predictions.pkl -gold_rels ../PURE/data/test/gold_relins.pkl -boost_precision 1 -boost_recall 1 -topk 1
# fi 

# cd ../combine_prediction
# # ==================== COMBINED PREDICTION WITH CONTAINER AND PURE =========
# if [ "$combine_dev" = "1" ]
# then
#   python container_pipeline.py -targets ../container/temp/dev/targets.pred -rels ../PURE/temp/rel/dev/predictions.pkl -gold_rels ../PURE/data/dev/gold_relins.pkl -boost_precision $boost_precision -boost_recall $boost_recall
# fi

# if [ "$combine_test" = "1" ]
# then
#   python container_pipeline.py -targets ../container/temp/test/targets.pred -rels ../PURE/temp/rel/test/predictions.pkl -gold_rels ../PURE/data/test/gold_relins.pkl -boost_precision $boost_precision -boost_recall $boost_recall
# fi 

# ================== PAIR CONTAINEE AND CONTAINER WITHOUT PURE ===
# DEV 
python pair_containee_container.py -targets ../container/temp/dev/targets.pred -components ../containee/temp/dev/spans.pred -gold_rels ../PURE/data/dev/gold_relins.pkl

# TEST
python pair_containee_container.py -targets ../container/temp/test/targets.pred -components ../containee/temp/test/spans.pred -gold_rels ../PURE/data/test/gold_relins.pkl

# ==================== CONTAINER AND CONTAINEE FILTER WITH PURE ===
python two_filters_and_pure.py -targets ../container/temp/dev/targets.pred -components ../containee/temp/dev/spans.pred -rels ../PURE/temp/rel/dev/predictions.pkl  -gold_rels ../PURE/data/dev/gold_relins.pkl

python two_filters_and_pure.py -targets ../container/temp/test/targets.pred -components ../containee/temp/test/spans.pred -rels ../PURE/temp/rel/test/predictions.pkl  -gold_rels ../PURE/data/test/gold_relins.pkl

# ==================== one side prediction =========================
cd ../one-sided-experiments

python one_side_prediction.py -targets ../container/temp/dev/targets.pred -components ../containee/temp/dev/spans.pred  -gold_rels ../PURE/data/dev/gold_relins.pkl -mode close_target_bt

python one_side_prediction.py -targets ../container/temp/test/targets.pred -components ../containee/temp/test/spans.pred  -gold_rels ../PURE/data/test/gold_relins.pkl -mode close_target_bt

python one_side_prediction.py -targets ../container/temp/dev/targets.pred -components ../containee/temp/dev/spans.pred  -gold_rels ../PURE/data/dev/gold_relins.pkl -mode close_component_bt


python one_side_prediction.py -targets ../container/temp/test/targets.pred -components ../containee/temp/test/spans.pred  -gold_rels ../PURE/data/test/gold_relins.pkl -mode close_component_bt


python one_side_prediction.py -targets ../container/temp/dev/targets.pred -components ../containee/temp/dev/spans.pred  -gold_rels ../PURE/data/dev/gold_relins.pkl -mode pair

python one_side_prediction.py -targets ../container/temp/test/targets.pred -components ../containee/temp/test/spans.pred  -gold_rels ../PURE/data/test/gold_relins.pkl -mode pair


python one_side_prediction.py -targets ../container/temp/dev/targets.pred -components ../containee/temp/dev/spans.pred  -gold_rels ../PURE/data/dev/gold_relins.pkl -mode pair_close_target

python one_side_prediction.py -targets ../container/temp/test/targets.pred -components ../containee/temp/test/spans.pred  -gold_rels ../PURE/data/test/gold_relins.pkl -mode pair_close_target

python one_side_prediction.py -targets ../container/temp/test/targets.pred -components ../containee/temp/test/spans.pred  -gold_rels ../PURE/data/test/gold_relins.pkl -mode pair_close_component 

python one_side_prediction.py -targets ../container/temp/dev/targets.pred -components ../containee/temp/dev/spans.pred  -gold_rels ../PURE/data/dev/gold_relins.pkl -mode pair_close_target_and_component -analyze 1 


python one_side_prediction.py -targets ../container/temp/test/targets.pred -components ../containee/temp/test/spans.pred  -gold_rels ../PURE/data/test/gold_relins.pkl -mode pair_close_target_and_component -analyze 1 

