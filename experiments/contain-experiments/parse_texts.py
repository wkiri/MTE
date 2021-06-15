import os, sys, argparse, json, re, subprocess, glob, shutil
from os import makedirs, listdir
from os.path import exists, join, abspath, dirname
from sys import stdout

curpath=dirname(abspath(__file__))


def make_filelist(indir, outdir):
    # produce a filelist that contains a list of absolute paths of text fils to parse
    if not exists(outdir):
        makedirs(outdir)
    temp_files = [abspath(join(indir, file)) for file in listdir(indir) if file.endswith(".txt")]
    # filter files without Target or Component
    files = []
    for file in temp_files:
        # annfile = file.split(".txt")[0] + ".ann"
        # with open(annfile, "r") as f:
        #     text = f.read().strip()
        # if not (re.search("Element", text) or re.search("Mineral",text )) or not re.search("Target", text):
        #     continue
        files.append(file)
    print(f"{len(files)} files to parse")

    filelist_path = abspath(join(outdir, "filelist.txt"))

    print(f"Saving filelist to {filelist_path}")

    with open(filelist_path, "w") as f:
        f.write("\n".join(files))
    return filelist_path


def parse_with_ner( command_arguments, args, text_prop, ner_prop):
    # parsing with ner is tricky. using ner model with tokenization would actually change the tokenization results. For example, 'k-rich' is treated as a single token if ner model is used, but split into three tokens without any ner model. I don't know why this happens.  The tokenization results after using NER model decrease the number of entities from annotation that could be matched by the tokenized words. As a result, we still want to keep the tokenization when we do NER. To do this, we do two passes. The first pass do tokenization, and the second pass do ner annotation only.  

    # do parsing without ner first
    for filelist_path, outdir in command_arguments:
        
        command = f"java -cp * edu.stanford.nlp.pipeline.StanfordCoreNLP -outputFormat json -fileList {filelist_path} -outputDirectory {outdir} -prop {text_prop}"
        subprocess.run(command.split(), check = True)
        print(f"removing {filelist_path}")
        os.remove(filelist_path)

        print("create tokenized text files")
        tokfilelist = []
        tempdir = join(outdir, "temp")
        if not exists(tempdir):
            makedirs(tempdir)

        for jsonfile in glob.glob(join(outdir, "*.txt.json")):
            docname = jsonfile.split("/")[-1].split(".txt")[0]
            tokfile = join(tempdir, docname + '.txt')
            tokfilelist.append(tokfile)
            texts = []
            doc = json.load(open(jsonfile, "r"))
            for s in doc['sentences']:
                texts.append(" ".join([tok['word'] for tok in s['tokens']]))
            texts = "\n".join(texts)

            with open(tokfile, "w") as f:
                f.write(texts)

        print("Annotating with NER model")
        # first write tokfilelist

        tokfilelist_path = join(tempdir, 'filelist')
        with open(tokfilelist_path, "w") as f:
            f.write("\n".join(tokfilelist))

        command = f"java -cp * edu.stanford.nlp.pipeline.StanfordCoreNLP -outputFormat json -fileList {tokfilelist_path} -outputDirectory {tempdir} -prop {ner_prop} -quiet true"
        print(command)
        subprocess.run(command.split(), check = True)

        print("Collecting NERs")
        print(len(glob.glob(join(tempdir, "*.txt.json"))))
        for ner_file in glob.glob(join(tempdir, "*.txt.json")):
            docname = ner_file.split("/")[-1].split(".txt.json")[0]
            jsonfile = join(outdir, docname + ".txt.json")

            nerdoc = json.load(open(ner_file, "r"))
            ners = [tok['ner'] for s in nerdoc['sentences'] for tok in s['tokens']]
            doc = json.load(open(jsonfile, "r"))
            wordidx = 0 
            for s in doc['sentences']:
                for tok in s['tokens']:
                    tok['ner'] = ners[wordidx]
                    wordidx += 1


            with open(jsonfile, "w") as of:
                json.dump(doc, of)

        shutil.rmtree(tempdir)



                




def main(args):


    command_arguments = []
    for indir in args.indir:
        indir = abspath(indir)
        venue = indir.strip("/").split("/")[-1]
        outdir = join(abspath(args.outdir), venue)

        filelist_path = make_filelist(indir, outdir)
        command_arguments.append((filelist_path, outdir))
    os.chdir(args.corenlp_dir)

    text_prop = join(curpath, 'parse_texts.props') 
    ner_prop = join(curpath, 'parse_with_ner.props')


    if not args.use_trained_ner:
        for filelist_path, outdir in command_arguments:
            command = f"java -cp * edu.stanford.nlp.pipeline.StanfordCoreNLP -outputFormat json -fileList {filelist_path} -outputDirectory {outdir} -prop {text_prop}"
            
            subprocess.run(command.split(), check = True)
            print(f"removing {filelist_path}")
            os.remove(filelist_path)
    else:
        parse_with_ner(command_arguments, args, text_prop, ner_prop)



if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='call stanford corenlp to parse text file')
    parser.add_argument('--indir', nargs="+", required = True, help="directories that contains .txt files")

    parser.add_argument('--outdir', required = True, help="output directory")
    
    parser.add_argument('--corenlp_dir',required = True, help="directory of stanfordcorenlp")

    parser.add_argument('--use_trained_ner',default = 0, help = "whether annotate texts with a trained NER system")

    args = parser.parse_args()

    main(args)