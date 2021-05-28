import re, glob, sys, copy
from collections import Counter
from parse_annot_configs import accept_ner_labels

def add_to_queue(queue_entities, temp_word_dict, add_by_gold_label = 0):

    # word_dict = {text, sent_start_idx, sent_end_idx, sentid, doc_start_char, doc_end_char, gold_ner, predicted_ner}
    word_dict = copy.deepcopy(temp_word_dict)
    if not len(queue_entities):
        queue_entities.append(word_dict)
    else:
        # two words should be merged if either of the following is satisfied:
        #     1. two words are adjacent and share the same label 
        #     2. two words share the same label and are separated by an hyphen or underscore
        curlabel = word_dict["predicted_ner"] if not add_by_gold_label else word_dict["gold_ner"]
        
        lastlabel = queue_entities[-1]["predicted_ner"] if not add_by_gold_label else queue_entities[-1]["gold_ner"]
        lasttext = queue_entities[-1]["text"]

        if curlabel == "O":
            queue_entities.append(word_dict)
        else:
            if curlabel == lastlabel: # if same label then merge them into one entity
            
                queue_entities[-1]["text"] = f"{queue_entities[-1]['text']} {word_dict['text']}"
                queue_entities[-1]["lemma"] = f"{queue_entities[-1]['lemma']} {word_dict['lemma']}"

                queue_entities[-1]["sent_end_idx"] = word_dict["sent_end_idx"]
                queue_entities[-1]["doc_end_char"] = word_dict["doc_end_char"]
            elif len(queue_entities) >= 2 and (lasttext == "-" or lasttext == "_") and curlabel == queue_entities[-2][f"{'predicted' if not add_by_gold_label else 'gold'}_ner"]:
                # in this case, two words are separated by hyphen or underscore and they have the same label

                queue_entities[-2]["text"] = f"{queue_entities[-2]['text']}{queue_entities[-1]['text']}{word_dict['text']}"
                queue_entities[-2]["lemma"] = f"{queue_entities[-2]['lemma']}{queue_entities[-1]['lemma']}{word_dict['lemma']}"
                queue_entities[-2]["sent_end_idx"] = word_dict["sent_end_idx"]
                queue_entities[-2]["doc_end_char"] = word_dict["doc_end_char"]

                # remove queue_entities[-1]
                queue_entities.pop(-1)
            else:
                queue_entities.append(word_dict)



def get_docid(convfile):
    venue = convfile.split("/")[-2]
    if "lpsc" in convfile:
        year = re.findall(r"lpsc(\d+)", convfile)[0]
        docname = convfile.split("/")[-1].split(".txt")[0]
    elif "mpf" in convfile or "phx" in convfile:
        year, docname = re.findall(r"(\d+)_(\d+)", convfile.split("/")[-1])[0] 
    else:
        raise NameError(f"file must be from LPSC or MPF or PHX. Currently we have {convfile}")
    doc_id = f"{venue}_{year}_{docname}"
    return venue, year, docname, doc_id




def read_converted(converted_file):

    # this function reads the convrted file and collect entities from each doc
    # text_file is used to evaluate whether the charoffset corresponds to the correct word
    # text = open(text_file, "r", encoding = "ISO-8859-1").read()

    doc = {
            "sents": [], 
            "predicted_entities": [],
            "gold_entities":[], # although it is collected, THIS SHOULD NOT BE USED FOR EVALUATION! The reason is that it will not completely match the gold annotation since it is collected from the converted_file, which was produced from the brat_annotation. The current code that parses brat_annotation has tokenization issues (the words after tokenization may not form the gold span in the annotation) and does not handle the nested ner annotation issues, and so it will not make the gold annotation collected match exactly the gold annotation in the ann file. 
            "char2sentid":{}
        }

    with open(converted_file, "r") as f:
        sent_blocks = f.read().strip().split("\n\n")
        sents = []

        for  sent_block in sent_blocks:
            if sent_block.strip() == "": continue

            sent_block = sent_block.strip()
            lines = sent_block.split("\n")
            sentids = re.findall(r"\bsentid=(\d+)\b", lines[-1])
            assert len(sentids) == 1
            sentid = int(sentids[0])
            assert sentid == len(sents)

            assert len(lines[0].split("\t")) in [5,7]
            has_ner = len(lines[0].split("\t")) == 7 # if len is 7, then the columns would be word, lemma, gold ner label, predicted ner label, start_char, end_char, _. if len is 5, then the colums would be word, gold ner label, start char, end char, _
            # assert int(lines[-2].split("\t")[-1]) == 0 # check the last token is not continued    
            if not has_ner:
                sent_start_char = int(lines[0].split("\t")[2])
                sent_end_char = int(lines[-2].split("\t")[3])
            else:
                sent_start_char = int(lines[0].split("\t")[4])
                sent_end_char = int(lines[-2].split("\t")[5])


           
            sent = []
            gold_entities = []
            predicted_entities = []


            # entity = {
            #     "text":""
            #     "sent_start_idx":
            #     "sent_end_idx":
            #     "doc_start_char":
            #     "doc_end_char":
            #     "predicted_ner":
            #     "gold_ner":
            #     "lemma"
            # }

            sent_start_idx = 0
            for sent_start_idx, line in enumerate(lines[:-1]):

                line = line.strip()
                if line == "": continue
                items = line.split("\t")
                predicted_label = 'O'
                if not has_ner:
                    word, label, start_char, end_char, _ = items

                else: # contains an extra ner label predicted from the trained ner model. use the  
                    word, lemma, label, predicted_label, start_char, end_char, _ = items
                    assert predicted_label == 'O' or predicted_label in accept_ner_labels
                
                start_char = int(start_char)
                end_char = int(end_char)
                # print(f"WORD:{word}.\nTEXT:{text[start_char:end_char]}.")
                
                if has_ner:
                    word_dict = {
                        "text": word, 
                        "sent_start_idx":sent_start_idx,
                        "sent_end_idx": sent_start_idx + 1,
                        "sentid":sentid, 
                        "doc_start_char":start_char,
                        "doc_end_char": end_char,
                        "gold_ner":label, 
                        "predicted_ner": predicted_label,
                        "lemma":lemma
                    }
                else:
                    word_dict = {
                        "text": word, 
                        "sent_start_idx":sent_start_idx,
                        "sent_end_idx": sent_start_idx + 1,
                        "sentid":sentid, 
                        "doc_start_char":start_char,
                        "doc_end_char": end_char,
                        "gold_ner":label, 
                    }



                add_to_queue(gold_entities, word_dict, add_by_gold_label = 1)

                add_to_queue(predicted_entities, word_dict, add_by_gold_label = 0)
          
                start_char = int(start_char)
                end_char = int(end_char)
                sent_start_idx += 1

                sent.append(word)
            sents.append(sent)
            doc["char2sentid"][(sent_start_char, sent_end_char)] = sentid

            predicted_entities = [wd for wd in predicted_entities if wd["predicted_ner"] != "O"]
            if len(predicted_entities):

                doc["predicted_entities"].append(predicted_entities)

            gold_entities = [wd for wd in gold_entities if wd["gold_ner"] != "O"]

            if len(gold_entities):
                doc["gold_entities"].append(gold_entities)

        doc["sents"] = sents

    return doc

if __name__ == "__main__":
    # check number of entities

    # for converted_file in glob.glob("/uusoc/res/nlp/nlp/yuan/mars/data/converted/corpus-LPSC-with-ner/lpsc15c/*.txt"):
    
    #     text_file = "/uusoc/res/nlp/nlp/yuan/mars/data/corpus-LPSC/lpsc15c" + f"/{converted_file.split('/')[-1]}"

    #     doc = read_converted(converted_file, text_file)

    # # lpsc15: Counter({'Element': 1190, 'Mineral': 674, 'Target': 560})
    # # lpsc16: Counter({'Element': 1020, 'Mineral': 653, 'Target': 340})

    converted_file = "/uusoc/res/nlp/nlp/yuan/mars/data/converted/corpus-LPSC-with-ner/lpsc16/2942.txt"
    text_file = "/uusoc/res/nlp/nlp/yuan/mars/data/corpus-LPSC/lpsc15/2942.txt"
    doc = read_converted(converted_file)

    
    