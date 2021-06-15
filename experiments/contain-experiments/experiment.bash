# ===========
# 	preprocessing: use CoreNlp to tokenize, sentence split, and get system ners
# ===========
# parse texts with corenlp using trained NER to get system ners
# This would take some time 
python3 parse_texts.py \
	--indir \
		../../corpus-LPSC/lpsc15-C-raymond-sol1159-v3-utf8 \
		../../corpus-LPSC/lpsc16-C-raymond-sol1159-utf8/ \
		../../corpus-LPSC/mpf-reviewed+properties-v2/ \
		../../corpus-LPSC/phx-reviewed+properties-v2 \
	--outdir ../../parse-with-sysners \
	--corenlp_dir /uusoc/exports/scratch/yyzhuang/stanford-corenlp-4.2.0 \
	--use_trained_ner 1

# parse text files with corenlp without any ners
python3 parse_texts.py \
	--indir \
		../../corpus-LPSC/lpsc15-C-raymond-sol1159-v3-utf8 \
		../../corpus-LPSC/lpsc16-C-raymond-sol1159-utf8/ \
		../../corpus-LPSC/mpf-reviewed+properties-v2/ \
		../../corpus-LPSC/phx-reviewed+properties-v2 \
	--outdir ../../parse \
	--corenlp_dir /uusoc/exports/scratch/yyzhuang/stanford-corenlp-4.2.0

