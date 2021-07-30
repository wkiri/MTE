# make list 

mkdir data 

# train data 
find "$(cd ../../../corpus-LPSC/lpsc15-C-raymond-sol1159-v3-utf8; pwd)" -name "*.ann" | sort  | head -42 > 1.list
find "$(cd ../../../corpus-LPSC/lpsc15-C-raymond-sol1159-v3-utf8; pwd)" -name "*.txt" | sort | head -42 > 2.list
find "$(cd ../../../parse/lpsc15-C-raymond-sol1159-v3-utf8; pwd)" -name "*.txt.json" | sort | head -42 > 3.list
paste  -d "," 1.list  2.list 3.list > data/train.list

#dev data 
find "$(cd ../../../corpus-LPSC/lpsc15-C-raymond-sol1159-v3-utf8; pwd)" -name "*.ann" | sort  | tail -20 > 1.list
find "$(cd ../../../corpus-LPSC/lpsc15-C-raymond-sol1159-v3-utf8; pwd)" -name "*.txt" | sort | tail -20 > 2.list
find "$(cd ../../../parse/lpsc15-C-raymond-sol1159-v3-utf8; pwd)" -name "*.txt.json" | sort | tail -20 > 3.list
paste  -d "," 1.list  2.list 3.list > data/dev.list

# test data 
for name in lpsc16-C-raymond-sol1159-utf8 phx-reviewed+properties-v2 mpf-reviewed+properties-v2
do  
	find "$(cd ../../../corpus-LPSC/$name; pwd)" -name "*.ann" | sort  > 1.list
	find "$(cd ../../../corpus-LPSC/$name; pwd)" -name "*.txt" | sort  > 2.list
	find "$(cd ../../../parse/$name; pwd)" -name "*.txt.json" | sort  > 3.list
	paste  -d "," 1.list  2.list 3.list  > $name.list
done

cat lpsc16-C-raymond-sol1159-utf8.list phx-reviewed+properties-v2.list mpf-reviewed+properties-v2.list > data/test.list



rm *.list

# ==== CONTAINEE ===== 
cd containee 
python3 make_train_dev_test.py --train_inlist ../data/train.list --dev_inlist ../data/dev.list --test_inlist ../data/test.list --max_len 512

modelSaveDir=./temp

python3 train.py  --train_dir ins/train --val_dir ins/dev/gold_ner  --lr 0.00001 --epoch 10  --analyze_dev 1 --model_save_dir $modelSaveDir

# eval dev set 
mkdir $modelSaveDir/dev
python3 predict.py --modelfile "$modelSaveDir/trained_model.ckpt" --test_dir ins/dev/gold_ner --outdir $modelSaveDir/dev 

# eval test 
mkdir $modelSaveDir/test
python3 predict.py --modelfile "$modelSaveDir/trained_model.ckpt" --test_dir ins/test/gold_ner --outdir $modelSaveDir/test

# ====== CONTAINER ========
cd ../container

python3 make_train_dev_test.py --train_inlist ../data/train.list --dev_inlist ../data/dev.list --test_inlist ../data/test.list --max_len 512

modelSaveDir=./temp

python3 train.py  --train_dir ins/train --val_dir ins/dev/gold_ner  --lr 0.000005 --epoch 10  --analyze_dev 1 --model_save_dir $modelSaveDir

# eval dev set 
mkdir $modelSaveDir/dev
python3 predict.py --modelfile "$modelSaveDir/trained_model.ckpt" --test_dir ins/dev/gold_ner --outdir $modelSaveDir/dev 

# eval test 
mkdir $modelSaveDir/test
python3 predict.py --modelfile "$modelSaveDir/trained_model.ckpt" --test_dir ins/test/gold_ner --outdir $modelSaveDir/test

cd ../one-sided-experiments
python make_eval_set.py --test_inlist ../data/test.list

python prediction.py --targets ../container/temp/test/targets.pred --components ../containee/temp/test/components.pred --entity_linking_method closest_container_closest_containee --outdir ./temp  


python ../eval.py --pred_relins ./temp/test/relations.pred --gold_relins ./temp/relation_eval/test/gold_relins.pkl 
