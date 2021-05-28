import json, glob


# def correct_offset(token_begin, token_end, text, last_token_org_end, diff_offset):
#     # diff_offset: how many characters before have been removed 
#     diff = token_end - token_begin

#     if diff > len(text):
#         # decrease token end, and diff_offset should be increased 
#         token_begin -= diff_offset
#         diff_offset += diff - len(text)
#         token_end -= diff_offset
#     else:
#         # if distance between token begin and token end is equal or less than the length of text, then increase token end, and decrease diff_offset   
#         token_begin -= diff_offset
#         diff_offset -= len(text) - diff 
#         token_end -= diff_offset

#     return token_begin, token_end, diff_offset

def correct_offset(tokens, text):
    last_modfied_end = None
    for i, token in enumerate(tokens):
        token_org_begin, token_org_end = token["characterOffsetBegin"], token['characterOffsetEnd']
        
        if i == 0:
            token_modified_begin = token_org_begin
        else:
            for token_modified_begin in range(last_modfied_end, len(text)):
                if text[token_modified_begin] != " ":
                    break
        token_modfied_end = token_modified_begin + len(token['word'])

        token["characterOffsetBegin"] = token_modified_begin
        token["characterOffsetEnd"] = token_modfied_end
        last_modfied_end = token_modfied_end


        print(f"org: ({token_org_begin}, {token_org_end}), modified: ({token_modified_begin}, {token_modfied_end}), text: ({token['word']})")




for corenlp_file in glob.glob("/uusoc/res/nlp/nlp/yuan/mars/data/stanford-parse/corpus-LPSC/*/*.json"):
    text_file = f"/uusoc/res/nlp/nlp/yuan/mars/data/corpus-LPSC/{corenlp_file.split('/')[-2]}/{corenlp_file.split('/')[-1][:-5]}"
    text_file = "/uusoc/res/nlp/nlp/yuan/mars/data/corpus-LPSC/mpf-reviewed+properties-v2/1998_1186.txt"
    corenlp_file = "/uusoc/res/nlp/nlp/yuan/mars/data/stanford-parse/corpus-LPSC/mpf-reviewed+properties-v2/1998_1186.txt.json"
    doc = json.load(open(corenlp_file, "r"))

    text = open(text_file).read()
    import stanza
    nlp = stanza.Pipeline('en',processors='tokenize,ssplit', use_gpu = False) 
    doc = nlp(text)
    for sent in doc.sentences:
        print(' '.join([k.text for k in sent.tokens]))

    print(text_file, corenlp_file)
    stop = 0 
    diff_offset = 0 
    for sent in doc["sentences"]:
        last_token_org_end = None # record the last work's corenlp token_end, use to compute the space between last token and this token 
        correct_offset(sent["tokens"],text)
        for token in sent["tokens"]:
            token_begin, token_end =(token["characterOffsetBegin"], token["characterOffsetEnd"])
           

            print(token_begin, token_end, text[token_begin:token_end],token["word"] )


            if token["word"] != text[token_begin:token_end]:
                stop = 1
            if stop:
                print("STOP!")
                break
        if stop:break
    if stop:
        break



