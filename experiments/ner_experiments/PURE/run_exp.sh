export CUDA_VISIBLE_DEVICES=1;
declare -a venues=( "lpsc16-C-raymond-sol1159-utf8" "mpf-reviewed+properties-v2" "phx-reviewed+properties-v2"
  )

python3 make_train_dev_test.py --test_venues "${venues[@]}"  --use_component 1 

# train 
python run_entity.py \
    --do_train --do_eval \
    --learning_rate=1e-5 --task_learning_rate=5e-4 \
    --train_batch_size=10 \
    --context_window 0 \
    --task mars \
    --data_dir ./data \
    --model bert-base-uncased \
    --output_dir ./temp --num_epoch 20

python run_entity.py \
	--do_eval \
    --eval_test \
    --context_window 0 \
    --task mars \
    --data_dir ./data \
    --model bert-base-uncased \
    --output_dir ./temp --num_epoch 20

python make_purepred_to_instance.py --pred_file ./temp/ent_pred_dev.json --use_component 1 
python ../eval.py --pred_ners temp/ent_pred_dev.pkl --gold_ners data/dev_golds.pkl

python make_purepred_to_instance.py --pred_file ./temp/ent_pred_test.json --use_component 1 
python ../eval.py --pred_ners temp/ent_pred_test.pkl --gold_ners data/test_golds.pkl



