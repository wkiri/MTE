# # NER model

# # first convert brat annotation and train ner model 
# python3 convert_brat_annot.py --indir ../data/corpus-LPSC/lpsc15 ../data/corpus-LPSC/lpsc16 --outdir ../data/converted/corpus-LPSC/lpsc15 ../data/converted/corpus-LPSC/lpsc16 --stanford_dirs ../data/stanford-parse/corpus-LPSC/lpsc15 ../data/stanford-parse/corpus-LPSC/lpsc16


# # # train ner model 
# # bash train_ner.sh

# use train ner model to predict ner for the files again 
# python3 parse_text_files_with_ner.py --indir ../data/corpus-LPSC/lpsc15 ../data/corpus-LPSC/lpsc16 --outdir ../data/stanford-parse-with-ner/corpus-LPSC/lpsc15 ../data/stanford-parse-with-ner/corpus-LPSC/lpsc16 --stanford_dir /uusoc/exports/scratch/yyzhuang/stanford-corenlp-4.2.0

# parse text files with corenlp into json 
# python3 parse_text_files_with_ner.py --indir ../data/corpus-LPSC/mpf-reviewed+properties-v2/ ../data/corpus-LPSC/phx-reviewed+properties --outdir ../data/stanford-parse-with-ner/corpus-LPSC --stanford_dir /uusoc/exports/scratch/yyzhuang/stanford-corenlp-4.2.0




# parse text files with corenlp without ner 
python3 parse_without_ner.py --indir ../data/corpus-LPSC/mpf-reviewed+properties-v2/ ../data/corpus-LPSC/phx-reviewed+properties-v2 ../data/corpus-LPSC/lpsc15 ../data/corpus-LPSC/lpsc16 --outdir ../data/stanford-parse/corpus-LPSC --stanford_dir /uusoc/exports/scratch/yyzhuang/stanford-corenlp-4.2.0



# convert brat annotation with predicted ner 
# python3 convert_brat_annot.py --indir ../data/corpus-LPSC/lpsc15 ../data/corpus-LPSC/lpsc16 --outdir temp/data/converted/corpus-LPSC-with-ner/lpsc15 temp/data/converted/corpus-LPSC-with-ner/lpsc16 --stanford_dirs ../data/stanford-parse-with-ner/corpus-LPSC/lpsc15 ../data/stanford-parse-with-ner/corpus-LPSC/lpsc16 --stanford_has_ner_prediction 1

python3 convert_brat_annot_to_conll.py --indir ../data/corpus-LPSC/mpf-reviewed+properties-v2/ ../data/corpus-LPSC/phx-reviewed+properties --outdir ../data/converted/corpus-LPSC-with-ner --stanford_dirs ../data/stanford-parse-with-ner/corpus-LPSC/mpf-reviewed+properties-v2 ../data/stanford-parse-with-ner/corpus-LPSC/phx-reviewed+properties --stanford_has_ner_prediction 1


# make train, dev and test examples for relation model 
cd relation_model
bash run_exp.sh
# train and test the relation model 