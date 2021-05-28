

import os, sys, argparse, json, re
from os import makedirs, listdir
from os.path import exists, join, abspath, dirname
from sys import stdout
import subprocess

curpath=dirname(abspath(__file__))
from parse_annot_configs import accept_ner_labels



if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='call stanford corenlp to parse text file')
    parser.add_argument('--indir', nargs="+", required = True, help="directories that contains .txt files")

    parser.add_argument('--outdir', required = True, help="output directory")
    
    parser.add_argument('--stanford_dir',required = True, help="directory of stanfordcorenlp")

    args = parser.parse_args()


    def make_filelist(indir, outdir):
        if not exists(outdir):
            makedirs(outdir)
        temp_files = [abspath(join(indir, file)) for file in listdir(indir) if file.endswith(".txt")]
        # filter files without accept_ner_labels
        files = []

        for file in temp_files:
            annfile = file.split(".txt")[0] + ".ann"
            with open(annfile, "r") as f:
                text = f.read().strip()
            if not (re.search("Element", text) or re.search("Mineral",text )) or not re.search("Target", text):
                continue
            files.append(file)
        print(len(files))

        filelist_path = abspath(join(outdir, "filelist.txt"))
        with open(filelist_path, "w") as f:
            f.write("\n".join(files))
        return filelist_path




    command_arguments = []
    for indir in args.indir:
        indir = abspath(indir)
        venue = indir.strip("/").split("/")[-1]
        outdir = join(abspath(args.outdir), venue)

        print(f"processing files from {indir}")
        filelist_path = make_filelist(indir, outdir)
        command_arguments.append((filelist_path, outdir))

       
    os.chdir(args.stanford_dir)

    for filelist_path, outdir in command_arguments:

        command = f"java -cp * edu.stanford.nlp.pipeline.StanfordCoreNLP -outputFormat json -fileList {filelist_path} -outputDirectory {outdir} -prop {join(curpath, 'parse_without_ner.props')}"
        try:
            subprocess.run(command.split(), check = True)
        except:
            pass
        finally:
            os.remove(filelist_path)



