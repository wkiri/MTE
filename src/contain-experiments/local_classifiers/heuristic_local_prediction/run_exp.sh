
mode=EM
python closest_pred.py -spans ../contained/temp/$mode/test/$mode.spans.pred -rels ../relation_model/temp/EM/test/EM.rels.pred -gold_rels ../relation_model/rels/test/EM.annotated_gold_relins.pkl




mode=T
python closest_pred.py -spans ../contained/temp/$mode/test/$mode.spans.pred -rels ../relation_model/temp/EM/test/EM.rels.pred -gold_rels ../relation_model/rels/test/EM.annotated_gold_relins.pkl
TUPLE-LEVEL EVAL of combined prediction: precison: 66.20, recall: 58.75, f1: 62.25
INSTANCE-LEVEL EVAL of combined prediction: precision: 59.26, recall: 50.00, f1: 54.24