#!/usr/bin/env python

import os, yaml, sys, subprocess, json

# get output_file from sys.argv
def get_output_file():
      output_file = None
      for idx, arg in enumerate(sys.argv):
        if arg == "-o" or arg == "--output":
            output_file = sys.argv[idx+1]
        elif arg.startswith("--output="):
            output_file = arg[9:]
      return output_file

# get output_format from sys.argv
def get_output_format():
      output_format = None
      for idx, arg in enumerate(sys.argv):
        if arg == "-t" or arg == "--to":
            output_format = sys.argv[idx+1]
        elif arg.startswith("--to=") and len(arg) > 5:
            output_format = arg[5:]
      return output_format

# check output_format 
def check_output_format(output_format, output_file, meta):
    if output_format is None:
        if output_file is not None and "." in output_file:
            split_value = output_file.split(".", 1)
            output_format = split_value[1]
            if "pdf" in output_format:
                output_format = "pdf"
            if  "tex" in output_format:
                output_format = "latex"
        else:
            if isinstance(meta, dict) and len(meta) != 0:
                meta_key = list(meta.keys())[0]
                meta_val = meta[meta_key]
                if "to" in meta_val.keys() or "output" in meta_val.keys():
                    output_format = meta_key
                else:
                    sys.exit("panrun: [WARNING] defaulting to the YAML for output format '{}' \n\n"\
                        "but pandoc may not default to the same format.\n"\
                        "It is recommended to add a `to:` or `output:` field to your YAML.".format(output_format))
            else:
                sys.exit("Could not find any output format in YAML.")
    return output_format



 
# get all pandoc options
def get_pandoc_opts():
    command = ['pandoc', '--bash-completion']
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    first_split = result.stdout.split('opts="', 1)
    last_split = first_split[1].split('"', 1)
    opts = last_split[0].split(' ')
    clean_list = []
    for opt in opts:
        if '--' in opt:
            clean_list.append(opt[2:])
    return clean_list

# convert a meta-hash to an arguments-array
def get_args(meta):
   pandoc_opts = get_pandoc_opts()   
   # print(pandoc_opts)
   # print(meta)
   args = []
   for key, val in meta.items():
       # check whether `key` is an option that can be
       # used with the installed pandoc version
        opt = None
        if key in pandoc_opts:
            opt = key
            # print("found",opt)

        if opt is not None and val is not None:
            args.append("--"+opt)
        if isinstance(val, bool):
            break
        else:
            args.append(val)
        
   if "pandoc_args" in meta.keys():
        print("args.concat more_args")
   return args


# determine input file
def get_input_file():
    input_file = None
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if input_file is None or input_file[0] == "-":
        sys.exit("Usage: panrun input.md [pandoc-options]\n\n"\
        "Looking for default.yaml etc. in #{data_dir_name}\n"\
        "For more info, see https://github.com/mb21/panrun")
    return input_file

# load and merge various metadata
def get_meta_yaml_from_input_file(input_file):
    # Read YAML in markdown between 2 '---'
    stream = open(input_file, "r")
    docs = yaml.safe_load_all(stream)
    meta_yaml_from_input_file = None
    for idx, doc in enumerate(docs):
        if isinstance(doc, dict) and idx < 1:
            meta_yaml_from_input_file = doc
        else:
            break
    return meta_yaml_from_input_file

def check_type_from_meta_yaml(meta_yaml):
    type_doc = None
    if "type" in meta_yaml.keys():
        type_doc = meta_yaml["type"]
    return type_doc

def get_meta_output_from_load_yaml(meta_yaml):
    meta_output = {}
    if "output" in meta_yaml.keys():
        meta_output = meta_yaml["output"]
    return meta_output

def get_panrun_dir_path():
    home_path = os.path.expanduser("~")
    return os.path.join(home_path, '.panrun')

# try to load default YAML from other files and merge it with local YAML
def get_meta_from_other_file(meta_yaml, type_doc):
    if type(type_doc) != str:
        type_doc = "default"
    data_dir = get_panrun_dir_path()
    arr = [".", "..", "/", '\\']
    file_name = None
    if any(val in type_doc for val in arr):
       if os.path.exists(type_doc):
            file_name = type_doc
       else:
            sys.exit("Could not find file {}".format(type_doc))
    else:
        # look in ~/.panrun/
        file_path = os.path.join(data_dir, type_doc + ".yaml")
        if os.path.exists(file_path):
            file_name = file_path
    meta_file_panrun, args = [{},[]]
    if file_name is not None:
        meta_file_panrun = get_meta_yaml_from_input_file(file_name)
        args = ["--metadata-file", file_name]
    
    if meta_file_panrun is not None:
        for key, _ in meta_file_panrun.items():
            if key in meta_yaml.keys():
                meta_yaml[key].update(meta_file_panrun[key])
    return [meta_yaml, args]

# lookup format in meta, else try various rmarkdown formats
def check_meta_out(meta, output_format):
    meta_out = {}
    output_format_document = output_format + "_document"
    output_format_presentation = output_format + "_presentation"
    if output_format in meta.keys():
        meta_out = meta[output_format]
    elif output_format == "latex" and "pdf_document" in meta.keys():
        meta_out = meta["pdf_document"]
    elif output_format_document in meta.keys():
        meta_out = meta[output_format + "_document"]
    elif output_format_presentation in meta.keys():
        meta_out = meta[output_format + "_presentation"]
    else:
        sys.exit("Could not find YAML key for detected output format {}".format(output_format))
    return meta_out

if __name__ == "__main__":
  # calling function

  input_file = get_input_file()
  # print(input_file)
  #
  # input.md

  meta_yaml_from_input_file = get_meta_yaml_from_input_file(input_file)
  # print(meta_yaml_from_input_file)
  #
  # {'title': 'The title', 'author': 'mjcc', 'date': '21 novembre 2021', 'lang': 'fr
  # ', 'note_type': 'reference', 'writing_type': 'draft', 'titlepage': True, 'titlep
  # age-rule-color': '0dd1ff', 'titlepage-background': 'src/img/TitlePageBackground.
  # png', 'titlepage-text-color': 'eaecef', 'page-background': 'src/img/PageBackgrou
  # nd.png', 'colorlinks': '0dd1ff', 'toc': True, 'toc-own-page': True, 'mainfont':
  # 'DejaVuSerif', 'sansfont': 'DejaVuSans', 'linkcolor': 'blue', 'urlcolor': 'blue'
  # , 'listings-no-page-break': True, 'link-citations': True, 'code-block-font-size'
  # : '\\scriptsize', 'output': {'pdf': {'pdf-engine': 'xelatex', 'output': 'test.pd
  # f', 'from': 'markdown', 'template': 'src/templates/eisvogel', 'bibliography': 's
  # rc/bib/citation.bib', 'csl': 'src/bib/ieee.csl', 'citeproc': True, 'listings': Tru
  # e}}}

  type_doc = check_type_from_meta_yaml(meta_yaml_from_input_file)
  # print(type_doc)
  #
  # by exemple if add type: letter in meta yaml
  # letter
  # else
  # None

  meta_output = get_meta_output_from_load_yaml(meta_yaml_from_input_file)
  # print(meta_output)
  #
  # {'pdf': {'pdf-engine': 'xelatex', 'output': 'test.pdf', 'from': 'markdown', 'tem
  # plate': 'src/templates/eisvogel', 'bibliography': 'src/bib/citation.bib', 'csl': '
  # src/bib/ieee.csl', 'citeproc': True, 'listings': True}}

  meta, file_arg = get_meta_from_other_file(meta_output, type_doc)
  # print(meta)
  #
  #   {'pdf': {'pdf-engine': 'xelatex', 'output': 'test.pdf', 'from': 'markdown', 'tem
  # plate': 'src/templates/eisvogel', 'bibliography': 'src/bib/citation.bib', 'csl': '
  # src/bib/ieee.csl', 'citeproc': True, 'listings': True}}
  #
  # print(file_arg)
  #
  # if .panrun/default.yaml exist
  # ['--metadata-file', '~/.panrun/default.yaml']
  # if type: letter in input_file and .panrun/letter.yaml exist
  # ['--metadata-file', '~/.panrun/letter.yaml']
  # else :
  # []

  output_file = get_output_file()
  # print(output_file)
  #
  # if python panrun.py input.md -o test.pdf
  # test.pdf
  # else
  # None

  output_format = get_output_format()
  # print(output_format)
  #
  # if python panrun.py input.md -t pdf
  # pdf 
  # else
  # None

  output_format = check_output_format(output_format, output_file, meta)
  # print(output_format)
  #
  # for python panrun.py input.md
  # pdf
  # python panrun.py input.md -t pdf -o test.pdf
  # pdf
  # python panrun.py input.md -o test.pdf
  # pdf


  meta_out = check_meta_out(meta, output_format)
  # print(meta_out)
  #
  # python panrun.py input.md -t pdf -o test.pdf
  #  {'pdf-engine': 'xelatex', 'output': 'test.pdf', 'from': 'markdown', 'template':
  # 'src/templates/eisvogel', 'bibliography': 'src/bib/citation.bib', 'csl': 'src/bib/
  # ieee.csl', 'citeproc': True, 'listings': True}

  args = get_args(meta_out)
  # print(args)
  #
  # ['--pdf-engine', 'xelatex', '--output', 'test.pdf', '--from', 'markdown', '--tem
  # plate', 'src/templates/eisvogel', '--bibliography', 'src/bib/citation.bib', '--csl
  # ', 'src/bib/ieee.csl', '--citeproc']

  command = ["pandoc", input_file] + args + file_arg + sys.argv[2:]
  # print(' '.join(command))
  #
  #   pandoc input.md --pdf-engine xelatex --output test.pdf --from markdown --templat
  # e src/templates/eisvogel --bibliography src/bib/citation.bib --csl src/bib/ieee.cs
  # l --citeproc
  # process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
  stdout, stderr = process.communicate()
  if process.returncode != 0:
        print("Fail ! : {}".format(stderr))
  else:
    print("Success !")
