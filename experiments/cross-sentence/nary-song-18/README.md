FROM https://github.com/freesunshine0316/nary-grn
# *N*-ray Relation Extraction using Graph State LSTM

This repository corresponds to code for "[N-ary Relation Extraction using Graph State LSTM](https://arxiv.org/abs/1808.09101)", which has been accpeted by EMNLP 2018.

Subdirectories "bidir_dag_lstm" and "gs_lstm" contains our bidrectional DAG LSTM baseline and graph state LSTM (we recently rename it as graph recurrent network, GRN), respectively. 

## Important config options

There are several key options in our config file:

### class_num

The value can be either 5, which corresponds to the normal binary classification setting (Table 3 and 5 in our paper), or the multi-label classification setting (Table 6 in our paper).
The original relation set has 5 relations: 'resistance or non-response', 'sensitivity', 'response', 'resistance', 'None'.
For binary setting, we follow Peng et al., (2017) to group the first four relations into one relation.
More details can be found [here](https://github.com/freesunshine0316/nary-grn/blob/master/gs_lstm/G2S_data_stream.py#L26)

Note that this is somehow confusing, as we also have two datasets: "binary" and "ternary".
But this option has nothing to do with dataset selection.

### train_path

This option actually controls dataset selection.
It points to a "fof" (file of file), a file containing the paths of all associated files.
One example "fof" (train_list_0) can be:
```
/path-to-peng-data/drug_gene_var/1/data_graph_1
/path-to-peng-data/drug_gene_var/1/data_graph_2
/path-to-peng-data/drug_gene_var/2/data_graph_1
/path-to-peng-data/drug_gene_var/2/data_graph_2
/path-to-peng-data/drug_gene_var/3/data_graph_1
/path-to-peng-data/drug_gene_var/3/data_graph_2
/path-to-peng-data/drug_gene_var/4/data_graph_1
/path-to-peng-data/drug_gene_var/4/data_graph_2
```
and correspondingly, the test "fof" (test_list_0) can be:
```
/path-to-peng-data/drug_gene_var/0/data_graph_1
/path-to-peng-data/drug_gene_var/0/data_graph_2
```

We do 5-fold cross validation, so there should be 5 training "fof"s and 5 testing "fof"s, respectively.

### only_single_sent

This is a bool flag (true or false) for controling whether to take only the single-sentence instances.
Setting it to true corresponds to the results of column "Single" in Table 3 and 5 of our paper, otherwise that corresponds to the results of column "Cross".

## Important directories

### Bidir DAG LSTM

Our implementation of [Peng et al., (2017)](https://www.cs.jhu.edu/~npeng/papers/TACL_17_RelationExtraction.pdf), but with a main difference on how to utilize the edge labels. Section 3.3 of our paper describes the differences.
Our DAG LSTM is implemented based on tf.while_loop, thus it is highly effecient without redundency. 

### GS LSTM (GRN)

Our graph-state LSTM model.

## How to run

Simply goes to the corresponding directory, and execute train.sh or decode.sh for training and evaluation, respectively. 
You may need to modify both scripts before executing. The hyperparameters and other settings are in config.json.

We used 5-fold cross validation to conduct our experiment. If your dataset has a training/dev/test separation, just ignore the words below.
To make things a little bit easier, we use file-of-file, where the first-level files store the locations of the data. One example is "train_list_0" and "test_list_0" in [./gs_lstm/data](./gs_lstm/data), where each line points to a file address. Our data has been segmented into 5 folds by Peng et al., thus we simply follow it.
You need to modify both "train_list_0" and "test_list_0" and make the rest, such as "train_list_1" and "test_list_1"

Other scripts within [./gs_lstm/data](./gs_lstm/data) is for extracting pretrained word embeddings. We use Glove-100d pretrained embeddings. 

For more questions, please create a issue and I'll handle it as soon as possible.

## Data

We put the data by Peng et al., (2017) inside [this repository](./peng_data) for easy access for others.

## Cite

Please cite this bib:
```
@inproceedings{song2018n,
  title={N-ary Relation Extraction using Graph-State LSTM},
  author={Song, Linfeng and Zhang, Yue and Wang, Zhiguo and Gildea, Daniel},
  booktitle={Proceedings of the 2018 Conference on Empirical Methods in Natural Language Processing},
  pages={2226--2235},
  year={2018}
}
```

