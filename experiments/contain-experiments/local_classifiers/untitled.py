
# things to get 
input_ids = []
span1_bert_start_idx = -1
span1_bert_end_idx = -1
span2_bert_start_idx = -1
span2_bert_end_idx = -1

success = 1 # whether insering type markers is successful
# get sentence input ids
input_ids, tokidx2bertidx = get_input_ids(tokenizer, span1.sent_toks, max_len = max_len)

# check if the spans of entity1 and entit2 exceed the range of max_len after tokenization
if span1.sent_end_idx > len(tokidx2bertidx) or span2.sent_end_idx > len(tokidx2bertidx):
    success = 0
    return success

#find span_bert_start_idx and span_bert_end_idx of each entity in the tokenized sentence
span1_bert_start_idx = tokidx2bertidx[span1.sent_start_idx][0]
span1_bert_end_idx = tokidx2bertidx[span1.sent_end_idx - 1][-1]
span2_bert_start_idx = tokidx2bertidx[span2.sent_start_idx][0]
span2_bert_end_idx = tokidx2bertidx[span2.sent_end_idx - 1][-1]

# now start to insert type markers
subj_start_marker = f"<S:{ner2markers[span1.ner_label]}>"
subj_end_marker = f"</S:{ner2markers[span1.ner_label]}>"
obj_start_marker = f"<O:{ner2markers[span2.ner_label]}>"
obj_end_marker = f"</O:{ner2markers[span2.ner_label]}>"

subj_sids, subj_eids, obj_sids, obj_eids = [ tokenizer.encode(k, add_special_tokens = False) for k in [subj_start_marker, subj_end_marker, obj_start_marker, obj_end_marker]]

if len(subj_sids) + len(subj_eids) + len(obj_sids) + len(obj_eids) + len(input_ids) > max_len:
    diff = len(subj_sids) + len(subj_eids) + len(obj_sids) + len(obj_eids) + len(input_ids) - max_len

    prespan_end = min(span1_bert_start_idx, span2_bert_start_idx)

    posspan_start = max(span1_bert_end_idx, span2_bert_end_idx)

    prespan_ids = input_ids[:prespan_end]
    posspan_ids = input_ids[posspan_start:]
    midspan_ids = input_ids[prespan_end:posspan_start]

    new_prespan_ids, new_posspan_ids, diff = truncate(prespan_ids, posspan_ids, diff) 

    if diff > 0:
        success = 0 
        return success
    
    # modify span1_bert_start_idx, ... 
    shrink_length = len(prespan_ids) - len(new_prespan_ids)
    span1_bert_start_idx -= shrink_length
    span2_bert_start_idx -= shrink_length
    span1_bert_end_idx -= shrink_length
    span2_bert_end_idx -= shrink_length
    input_ids = new_prespan_ids + midspan_ids + new_posspan_ids

sorted_loc = sorted([(span1_bert_start_idx,span1_bert_end_idx, "subj_start", "subj_end"), (span2_bert_start_idx, span2_bert_end_idx, "obj_start", "obj_end")], key = lambda x: x[0])

queue = [sorted_loc[0][0], sorted_loc[0][1], sorted_loc[1][0], sorted_loc[1][1]]
names = [sorted_loc[0][2], sorted_loc[0][3], sorted_loc[1][2], sorted_loc[1][3]]

new_inputids = []
for i, k  in enumerate(input_ids):
    if len(queue) and i == queue[0]:
        while len(queue) and i == queue[0]:
            if names[0] == "subj_start": 
                span1_bert_start_idx = len(new_inputids) 

                new_inputids.extend(subj_sids)
                new_inputids.append(k)
            elif names[0] == "subj_end":
                new_inputids.extend(subj_eids)
                span1_bert_end_idx = len(new_inputids)
                new_inputids.append(k)
            elif names[0] == "obj_start":
                span2_bert_start_idx = len(new_inputids)
                new_inputids.extend(obj_sids)
                new_inputids.append(k)
            else:
                new_inputids.extend(obj_eids)
                span2_bert_end_idx = len(new_inputids)
                new_inputids.append(k)
            queue.pop(0)
            names.pop(0)
    else:
        new_inputids.append(k)

input_ids = new_inputids
span1_bert_start_idx = span1_bert_start_idx
span2_bert_start_idx = span2_bert_start_idx
span1_bert_end_idx = span1_bert_end_idx
span2_bert_end_idx = span2_bert_end_idx

assert all([k >= 0 for k in [span1_bert_start_idx, span2_bert_start_idx, span1_bert_end_idx, span2_bert_end_idx]])

left_bracket_id = tokenizer.encode("<", add_special_tokens = False)[0]
right_bracket_id = tokenizer.encode(">", add_special_tokens = False)[0]

assert input_ids[span1_bert_start_idx] == left_bracket_id 

assert input_ids[span2_bert_start_idx] == left_bracket_id 

assert input_ids[span1_bert_end_idx - 1] == right_bracket_id 

assert input_ids[span2_bert_end_idx - 1] == right_bracket_id

return success