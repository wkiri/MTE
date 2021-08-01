autocmd Filetype markdown set tw=5
---
# Introduction

This directory contains the codes of modified PURE (the source code @https://github.com/princeton-nlp/PURE) for relation extraction over MTE dataset. 

To run experiments over the MTE dataset, we need to perform the following steps:

+ Split documents into TRAIN, DEV, and TEST documents 

+ Extract TRAIN, DEV, and TEST relation instances from documents 

+ Train PURE

+ Test PURE  

Below describe the details of each step. 

## 1. Split documents into TRAIN, DEV, TEST 

Given a collection of annotated documents (LPSC15 + LPSC16 + MPF + PHX), we first split them into Train, Dev and Test documents . The following script does so and generates train.list, dev.list and test.list in `./data/`

    mkdir data # make data folder 

    # make train data using first 42 lpsc15 documents
    find "$(cd ../../../corpus-LPSC/lpsc15-C-raymond-sol1159-v3-utf8; pwd)" -name "*.ann" | sort  | head -42 > 1.list
    find "$(cd ../../../corpus-LPSC/lpsc15-C-raymond-sol1159-v3-utf8; pwd)" -name "*.txt" | sort | head -42 > 2.list
    find "$(cd ../../../parse/lpsc15-C-raymond-sol1159-v3-utf8; pwd)" -name "*.txt.json" | sort | head -42 > 3.list
    paste  -d "," 1.list  2.list 3.list > data/train.list

    # make dev data using the last 20 lpsc15 documents 
    find "$(cd ../../../corpus-LPSC/lpsc15-C-raymond-sol1159-v3-utf8; pwd)" -name "*.ann" | sort  | tail -20 > 1.list
    find "$(cd ../../../corpus-LPSC/lpsc15-C-raymond-sol1159-v3-utf8; pwd)" -name "*.txt" | sort | tail -20 > 2.list
    find "$(cd ../../../parse/lpsc15-C-raymond-sol1159-v3-utf8; pwd)" -name "*.txt.json" | sort | tail -20 > 3.list
    paste  -d "," 1.list  2.list 3.list > data/dev.list

    # make test data using lpsc16 + phx + mpf data 
    for name in lpsc16-C-raymond-sol1159-utf8 phx-reviewed+properties-v2 mpf-reviewed+properties-v2
    do  
        find "$(cd ../../../corpus-LPSC/$name; pwd)" -name "*.ann" | sort  > 1.list

        find "$(cd ../../../corpus-LPSC/$name; pwd)" -name "*.txt" | sort  > 2.list
        
        find "$(cd ../../../parse/$name; pwd)" -name "*.txt.json" | sort  > 3.list
        
        paste  -d "," 1.list  2.list 3.list  > $name.list
    done

    cat lpsc16-C-raymond-sol1159-utf8.list phx-reviewed+properties-v2.list mpf-reviewed+properties-v2.list > data/test.list

    rm *.list


--- 
## 2. Extract TRAIN, DEV, and TEST relation instances from documents

Given that documents have been split into TRAIN, DEV, and TEST  collections, we extract relation instances from these documents. The following script generates TRAIN, DEV and TEST relation instances and saves them to `data/train`, `data/dev`, and `data/test`. 

    python3 make_train_dev_test.py \
    --train_inlist data/train.list \
    --dev_inlist data/dev.list \
    --test_inlist data/test.list \
    --max_len 512

## 3. Train PURE

The following script trains a PURE model. 

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
    --num_train_epochs 20 \
    --context_window 0  \
    --max_seq_length 512    \
    --output_dir ./temp/rel/ \
    --eval_per_epoch 1 \
    --add_new_tokens

## 4. Test pure
Once we finish training PURE, we could proceed to predict relations over DEV data and TEST data. Predictions would be saved to `temp/rel_pred/dev` and `temp/rel_pred/test`

+ Predict for DEV: 
    - Predict: 

    ```
    python run_relation.py \
    --task mars\
    --do_eval --eval_test --eval_with_gold \
    --test_file ./data/dev/gold_ner/docs.json \
    --model bert-base-uncased \
    --do_lower_case \
    --eval_batch_size 10 \
    --context_window 0  \
    --max_seq_length 512  \
    --output_dir temp/rel \
    --add_new_tokens

    ```
    - Extract Predictions:

        Next we extract relation instances from PURE's predictions, which will be saved to temp/rel/dev/predictions.pkl. 

    ```
    python match_purepred_to_instance.py \
    --pred_file temp/rel/predictions.json \
    --outfile temp/rel/dev/predictions.pkl
    ```
    

+ Predict for TEST: 
    - Predict: 

    ```
    python run_relation.py \
    --task mars\
    --do_eval --eval_test --eval_with_gold \
    --test_file ./data/test/gold_ner/docs.json \
    --model bert-base-uncased \
    --do_lower_case \
    --eval_batch_size 10 \
    --context_window 0  \
    --max_seq_length 512  \
    --output_dir temp/rel \
    --add_new_tokens

    ```
    - Extract Predictions:

        Next we extract relation instances from PURE's predictions, which will be saved to temp/rel/test/predictions.pkl. 

    ```
    python match_purepred_to_instance.py \
    --pred_file temp/rel/predictions.json \
    --outfile temp/rel/test/predictions.pkl
    ```

## 5. Evaluate PURE

We finally evaluate PURE by comparing the extracted relations to gold relations. 

+ DEV:

```
  python ../unary_classifiers/eval.py \
  --pred_relins temp/rel/dev/predictions.pkl \
  --gold_relins data/dev/gold_relins.pkl 
```

+ TEST:

```
  python ../unary_classifiers/eval.py \
  --pred_relins temp/rel/test/predictions.pkl \
  --gold_relins data/test/gold_relins.pkl 
```



