
# map data to cdr format 
python transform_to_cdr_format.py --use_component 1

cd data_processing 
python process_mars.py 

python3 statistics.py --data ../data/mars/processed/train.data
python3 statistics.py --data ../data/mars/processed/dev.data
python3 statistics.py --data ../data/mars/processed/test.data

# train 
cd src
python3 eog.py --config ../configs/parameters_mars.yaml --train --gpu 1 --epoch 25