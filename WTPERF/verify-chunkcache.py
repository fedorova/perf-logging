#!/usr/bin/env python3

import argparse
import os
import os.path
import sys
from argparse import RawTextHelpFormatter




# Globals
#
# The chunk cache is a dictionary of dictionaries. One dictionary per object.
# An object is a file-id combination.
# A per-file dictionary contains chunks, keyed by their offsets.
#
chunkCacheAllFiles = {};

# Codes for various colors for printing of informational and error messages.
#
class color:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


class cacheOps:
    CHECK = 'check'
    ALLOC = 'allocate'
    INSERT = 'insert'

def get_tokens(line):

    opAndElse = line.split(":");

    print("Here");

    if (len(opAndElse) < 2):
        print(color.BOLD + color.RED + "Could not parse:\n" + line + color.END);
        raise Exception("Split 1");

    op = opAndElse[0];
    print("Here");

    opParams = opAndElse[1].strip().split(",");
    if (len(opParams) < 3):
        print(color.BOLD + color.GREEN + "Could not parse:\n" + line + color.END);
        raise Exception("Split 2");

    fid = opParams[0].strip();
    print("Here");

    offsetWords = opParams[1].strip().split("=");
    print(offsetWords);
    if (len(offsetWords) < 2 or not (offsetWords[0] == "offset")):
        print(color.BOLD + color.PURPLE + "Could not parse:\n" + line + color.END);
        raise Exception("Split 3");
    offset = offsetWords[1];

    print("Here");
    sizeWords = opParams[2].strip().split("=");
    if (len(sizeWords) < 2 or not (sizeWords[0] == "size")):
        print(color.BOLD + color.BLUE + "Could not parse:\n" + line + color.END);
        raise Exception("Split 4");
    size = sizeWords[1];

    return op, fid, offset, size;

def process_cache_op(op, fid, offset, size):

    chunkCache = None;

    if fid not in chunkCacheAllFiles:
        chunkCacheAllFiles[fid] = {};

    chunkCache = chunkCacheAllFiles[fid];

    if (op == cacheOps.CHECK):
        process_check(chunkCache, offset, size);
    elif (op == cacheOps.ALLOC):
        process_alloc(chunkCache, offset, size);
    elif (op.startswith(cacheOps.INSERT)):
        process_insert(chunkCache, offset, size);

def process_line(line):

    if line.startswith(cacheOps.CHECK) or line.startswith(cacheOps.ALLOC) or \
        line.startswith(cacheOps.INSERT):
        try:
            op, fid, offset, size = get_tokens(line);
            print(op + " " + fid + " " + offset + " " + size);
            #process_cache_op(op, fid, offset, size);
        except:
            print(color.BOLD + color.RED + "Could not parse:\n" + line + color.END);
            sys.exit(-1);
            return;

def parse_file(fname):

    try:
        f = open(fname);
    except:
        print(color.BOLD + color.RED + "Could not open " + fname + color.END);
        sys.exit(1);

    for line in f.readlines():
        process_line(line);

def main():

    parser = argparse.ArgumentParser(description=
                                     "Parse chunk cache debug traces to check for correctness.",
                                     formatter_class=RawTextHelpFormatter);
    parser.add_argument('files', type=str, nargs='*',
                        help='Trace files to process');

    args = parser.parse_args();

    if (len(args.files) == 0):
        parser.print_help();
        sys.exit(1);

    for f in args.files:
        parse_file(f);


if __name__ == '__main__':
    main()
