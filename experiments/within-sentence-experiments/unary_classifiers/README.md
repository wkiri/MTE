# Introduction
This directory contains codes to train, test and evaluate the unary relation extraction approach which uses the Containee and Container model.

It contains three subdirectories:

* containee/:
    This directory contains codes for Containee model 

* container/:
    This directory contains codes
for Container model 

* unary_relation_extraction/:
    This directory contains codes that extract relations using predictions from Container and Containee together. 

Steps to train and test the models are described below. 

--- 
## 1. Split documents into Train, Dev and Test. 

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

## 2. Train and Test Containee Model 
Next we'll need to train a Containee model, which identifies if a Component is contained by some Target in the same sentence. In order to do this, we'll need to:

+ 2.1. Make Train, Dev and Test data for Containee
+ 2.2. Train a Containee 
+ 2.3. use trained Containee to make inference over Test data. 

which would be described one by one in the following sections.

### 2.1. Generate Training, Dev and Testing Data For Containee
We'll first generate training, dev and testing data for Containee, where each Component is assigned a label indicating whether the Component is contained by some Target in the same sentence.  Generated data would be put in `ins/train`, `ins/dev` and `ins/test`.

    cd containee 
    
    python3 make_train_dev_test.py \
    --train_inlist ../data/train.list \
    --dev_inlist ../data/dev.list \
    --test_inlist ../data/test.list \
    --max_len 512

### 2.2. Train Containee 
As data has been generated, we now train a Containee model. 

    python3 train.py  \
    --train_dir ins/train \
    --val_dir ins/dev/gold_ner  \
    --lr 0.00001 \
    --epoch 10 \
    --model_save_dir ./temp

### 2.3. Test Containee 
After training, we use Containee to make predictions for Dev and Test data. Predictions would be stored in `temp/dev/components.pred` and `temp/test/components.pred` (in pickle format).

+ Predict for Dev data: 

    ```
    python3 predict.py \
    --modelfile temp/trained_model.ckpt \
    --test_dir ins/dev/gold_ner \
    --outdir temp/dev 
    ```

+ Predict for Test data: 
    ```
    python3 predict.py \
    --modelfile temp/trained_model.ckpt \
    --test_dir ins/test/gold_ner \
    --outdir temp/test
    ```

So far, each Component has been asigned a label whether it is contained by some Target. 

Finally, let's go back to the parent directory: 

    cd ..

---

## 3. Train and Test Container Model
Next we'll need to train a Container, which identifies if a Target contains some Component(s) in the same sentence. Similar to what we did for Containee, we'll need to:

+ 3.1. Make Train, Dev and Test data for Container
+ 3.2. Train a Container
+ 3.3. use trained Container to make inference over Test data. 

### 3.1. Generate Training, Dev and Testing Data For Container

    cd container 
    
    python3 make_train_dev_test.py \
    --train_inlist ../data/train.list \
    --dev_inlist ../data/dev.list \
    --test_inlist ../data/test.list \
    --max_len 512

### 3.2. Train Container 
As data has been generated, we now train a Container model. 

    python3 train.py  \
    --train_dir ins/train \
    --val_dir ins/dev/gold_ner \
    --lr 0.000005 \
    --epoch 10 \
    --model_save_dir ./temp

### 3.3. Test Container 
After training, we use Container to make predictions for Dev and Test data. Predictions would be stored in `temp/dev/targets.pred` and `temp/test/targets.pred` (in pickle format).

+ Predict for Dev data: 

    ```
    python3 predict.py \
    --modelfile temp/trained_model.ckpt \
    --test_dir ins/dev/gold_ner \
    --outdir temp/dev 
    ```

+ Predict for Test data: 
    ```
    python3 predict.py \
    --modelfile temp/trained_model.ckpt \
    --test_dir ins/test/gold_ner \
    --outdir temp/test
    ```

So far, each Target has been asigned a label whether it contains any Component.

Finally, let's go back to the parent directory: 

    cd ..

---
## 4. Combine Container and Containee to Form Relations

So far we have used Containee to find Components that are contained (**Containee instances**) and Container to find Targets that contain (**Container instances**). Our final goal is to extract relations (Target, Contains, Component). As a result, we need another step to form relations from these Containee and Container instances, codes of which are in `unary_relation_extraction`. 

### 4.1. Extract Relations

Let's first move into the folder by: 
```
cd unary_relation_extraction/
```

The following script shows the command to predict relations using `targets.pred` (Container's predictions) and `components.pred` (Containee's predictions), with a specific grouping method (see detailed descriptions of methods in `prediction.py`).  The relations extracted will be saved to a pickle file `relations.pred`. 

+ Extract relations from DEV data:
    
    ```
    python prediction.py \
    --targets ../container/temp/dev/targets.pred \
    --components ../containee/temp/dev/components.pred \
    --entity_linking_method closest_container_closest_containee \
    --outdir ./temp/dev
    ```

+ Extract relations from TEST data:  
    
    ```
    python prediction.py \
    --targets ../container/temp/test/targets.pred \
    --components ../containee/temp/test/components.pred \
    --entity_linking_method closest_container_closest_containee \
    --outdir ./temp/test 
    ``` 

### 4.2. Evaluate Extracted Relations

Once relations are extracted, we proceed to evaluate them against the gold relations in 2 steps: 

+ Generate gold relations for evaluation, which is saved to a file named `gold_relins.pkl`: 

    - For DEV data:
        
        ```
        python make_eval_set.py \
        --test_inlist ../data/dev.list \
        --outdir ./temp/relation_eval/dev
        ```

    - For TEST data:

        ```
        python make_eval_set.py \
        --test_inlist ../data/test.list \
        --outdir ./temp/relation_eval/test
        ```


+ Evaluate the extracted relations against gold relations using `../eval.py`, which would print out the Precision, Recall and F1 scores :

    - Evaluate over DEV:

        ```
        python ../eval.py \
        --pred_relins ./temp/dev/relations.pred \
        --gold_relins ./temp/relation_eval/dev/gold_relins.pkl
        ```


    - Evaluate over TEST: 

        ```
        python ../eval.py \
        --pred_relins ./temp/test/relations.pred \
        --gold_relins ./temp/relation_eval/test/gold_relins.pkl 
        ```





 












