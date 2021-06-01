
mode=EM
python pipeline.py -spans ../contained/temp/EM/test/EM.spans.pred -rels ../PURE/temp/rel/predictions.pkl -gold_rels ../PURE/test/gold_relins.pkl -boost_precision 1 -boost_recall 1


mode=T
python pipeline.py -spans ../contained/temp/$mode/test/$mode.spans.pred -rels ../relation_model/temp/EM/test/EM.rels.pred -gold_rels ../relation_model/rels/test/EM.annotated_gold_relins.pkl -boost_precision 1 -boost_recall 1
