#!/usr/bin/env python
__authors__ = "Maxime Cordeiro"
__contact__ = "mjcc@tutanota.com"
__copyright__ = "MIT"
__date__ = "2021-11-28"
__version__ = "0.1.0"

import os
import yaml
import sys
from subprocess import Popen, PIPE, run
from typing import List, Dict, Any


# determine input file
def get_input_file() -> str:
    input_file: str = ""
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if input_file is None or input_file[0] == "-":
        sys.exit(
            "Usage: panrun input.md [pandoc-options]\n\n"
            "Lookstring in fonctioning for default.yaml etc. in #{data_dir_name}\n"
            "For more info, see https://github.com/mb21/panrun"
        )
    return input_file


# get output_file from sys.argv
def get_output_file() -> str:
    output_file: str = ""
    for idx, arg in enumerate(sys.argv):
        if arg == "-o" or arg == "--output":
            output_file = sys.argv[idx + 1]
        elif arg.startswith("--output="):
            output_file = arg[9:]
    return output_file


# get output_format from sys.argv
def get_output_format() -> str:
    output_format: str = ""
    for idx, arg in enumerate(sys.argv):
        if arg == "-t" or arg == "--to":
            output_format = sys.argv[idx + 1]
        elif arg.startswith("--to=") and len(arg) > 5:
            output_format = arg[5:]
    return output_format


# check output_format
def check_output_format(output_format: str, output_file: str, meta: Dict) -> str:
    if not output_format:
        if output_file and "." in output_file:
            split_value = output_file.split(".", 1)
            output_format = split_value[1]
            if "pdf" in output_format:
                output_format = "pdf"
            if "tex" in output_format:
                output_format = "latex"
        else:
            if isinstance(meta, dict) and len(meta) != 0:
                meta_key = list(meta.keys())[0]
                meta_val = meta[meta_key]
                if "to" in meta_val.keys() or "output" in meta_val.keys():
                    output_format = meta_key
                else:
                    sys.exit(
                        "panrun: [WARNING] defaulting to the YAML for output format '{}' \n\n"
                        "but pandoc may not default to the same format.\n"
                        "It is recommended to add a `to:` or "
                        "`output:` field to your YAML.".format(output_format)
                    )
            else:
                sys.exit("Could not find any output format in YAML.")
    return output_format


# get all pandoc options
def get_pandoc_opts() -> List[str]:
    command: List[str] = ["pandoc", "--bash-completion"]
    result = run(command, stdout=PIPE, stderr=PIPE, universal_newlines=True)
    first_split = result.stdout.split('opts="', 1)
    last_split = first_split[1].split('"', 1)
    opts = last_split[0].split(" ")

    clean_list: List[str] = []
    for opt in opts:
        if "--" in opt:
            clean_list.append(opt[2:])
    return clean_list


# convert a meta-hash to an arguments-array
def get_args(meta: Dict) -> List[str]:
    pandoc_opts: List[str] = get_pandoc_opts()
    # print(pandoc_opts)
    # print(meta)
    args: List[str] = []
    for key, val in meta.items():
        # check whether `key` is an option that can be
        # used with the installed pandoc version
        opt: str = ""
        if key in pandoc_opts:
            opt = key

        if opt and val:
            args.append("--" + opt)
        if isinstance(val, bool):
            break
        else:
            args.append(val)

    if "pandoc_args" in meta.keys():
        print("args.concat more_args")
    return args


def load_yaml_from_input_file(input_file: str) -> Any:
    # Read YAML in markdown between 2 '---'
    stream = open(input_file, "r")
    docs = yaml.safe_load_all(stream)
    return docs


# load and merge various metadata
def get_meta_yaml_from_input_file(input_file: str) -> Dict:
    docs: Dict = load_yaml_from_input_file(input_file)
    meta_yaml_from_input_file: Dict = {}
    for idx, doc in enumerate(docs):
        if isinstance(doc, dict) and idx < 1:
            meta_yaml_from_input_file = doc
        else:
            break
    return meta_yaml_from_input_file


def check_type_from_meta_yaml(meta_yaml: Dict) -> str:
    type_doc: str = ""
    if "type" in meta_yaml.keys():
        type_doc = meta_yaml["type"]
    return type_doc


def get_meta_output_from_load_yaml(meta_yaml: Dict) -> Dict:
    meta_output: Dict = {}
    if "output" in meta_yaml.keys():
        meta_output = meta_yaml["output"]
    return meta_output


def get_panrun_dir_path() -> str:
    home_path: str = os.path.expanduser("~")
    return os.path.join(home_path, ".panrun")


# try to load default YAML from other files and merge it with local YAML
def get_meta_from_other_file(meta_yaml: Dict, type_doc: str) -> List:
    if not type_doc:
        type_doc = "default"
    data_dir: str = get_panrun_dir_path()
    arr = [".", "..", "/", "\\"]
    file_name: str = ""
    if any(val in type_doc for val in arr):
        if os.path.exists(type_doc):
            file_name = type_doc
        else:
            sys.exit("Could not find file {}".format(type_doc))
    else:
        # look in ~/.panrun/
        file_path: str = os.path.join(data_dir, type_doc + ".yaml")
        if os.path.exists(file_path):
            file_name = file_path
    meta_file_panrun: Dict = {}
    args: List[str] = []
    if file_name:
        meta_file_panrun: Dict = get_meta_yaml_from_input_file(file_name)
        args = ["--metadata-file", file_name]

    if meta_file_panrun:
        for key, _ in meta_file_panrun.items():
            if key in meta_yaml.keys():
                meta_yaml[key].update(meta_file_panrun[key])
    return [meta_yaml, args]


# lookup format in meta, else try various rmarkdown formats
def check_meta_out(meta: Dict, output_format: str) -> Dict:
    meta_out: Dict = {}
    output_format_document: str = output_format + "_document"
    output_format_presentation: str = output_format + "_presentation"
    if output_format in meta.keys():
        meta_out = meta[output_format]
    elif output_format == "latex" and "pdf_document" in meta.keys():
        meta_out = meta["pdf_document"]
    elif output_format_document in meta.keys():
        meta_out = meta[output_format + "_document"]
    elif output_format_presentation in meta.keys():
        meta_out = meta[output_format + "_presentation"]
    else:
        sys.exit(
            "Could not find YAML key for detected output format {}".format(
                output_format
            )
        )
    return meta_out


def main() -> None:
    input_file: str = get_input_file()
    meta_yaml_from_input_file: Dict = get_meta_yaml_from_input_file(input_file)
    type_doc: str = check_type_from_meta_yaml(meta_yaml_from_input_file)
    meta_output: Dict = get_meta_output_from_load_yaml(meta_yaml_from_input_file)
    meta, file_arg = get_meta_from_other_file(meta_output, type_doc)
    output_file: str = get_output_file()
    output_format: str = get_output_format()
    output_format: str = check_output_format(output_format, output_file, meta)
    meta_out: Dict = check_meta_out(meta, output_format)
    args: List[str] = get_args(meta_out)
    command: List[str] = ["pandoc", input_file] + args + file_arg + sys.argv[2:]
    process = Popen(command, stdout=PIPE, stderr=PIPE, universal_newlines=True)
    _, stderr = process.communicate()
    if process.returncode != 0:
        print("Fail ! : {}".format(stderr))
    else:
        print("Success !")


if __name__ == "__main__":
    main()
