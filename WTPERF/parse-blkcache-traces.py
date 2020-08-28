#!/usr/bin/env python3

import argparse
import os
import os.path
import sys
from argparse import RawTextHelpFormatter

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

class supportedOps:
    CORRECTNESS = 'correctness'

class blockOps:
    INSERT = 'inserted'
    FOUND  = 'found'

class Block:
    def __init__(self, fname, offset, size):
        self.fname = fname;
        self.offset = off;
        self.size = size;

    def printBlock(self):
        print("\t" color.GREEN + self.fname + " " + str(self.offset) +
              " " + str(self.size);

blockCache = {};

def processCorrectness(line):

    fname = "";
    offset = 0;
    size = 0;

    if (not "[WT_VERB_BLKCACHE]" in line):
        return;

    words = line.split(" ");

    for word in words:
        if ("file:" in word):
            fname = word.split(":")[1];
        if ("offset=" in word):
            offset = word.split("=")[1];
        if ("size=" in word):
            size = word.split("=")[1];

    if (fname == "" or offset == 0 or size == 0):
        print(color.RED + "Invalid block parameters:\n\t" + line + color.END);
        return;

    block = Block(fname, offset, size);

    if (hash(block) in blockCache):
        print("Block already in cache:\n");
        block.printBlock();

    blockCache[hash(block)] = block;

    return;

def parse_file(fname, ops, startString):

    i = 0;
    startStringSeen = False;

    try:
        f = open(fname);
    except:
        print(color.BOLD + color.RED + "Could not open " + fname + color.END);
        sys.exit(1);

    if (len(startString) == 0):
        startStringSeen = True;

    for line in f.readlines():
        i+=1;
        if (not startStringSeen):
            if (startString in line):
                startStringSeen = True;
                print("Found " + startString + " on line " + str(i));
            else:
                continue;

        for op in ops:
            if (op == supportedOps.CORRECTNESS):
                processCorrectness(line);

def main():

    ops = [];

    parser = argparse.ArgumentParser(description=
                                     "Parse wt_verbose traces to collect information "
                                     "about the behaviour of the block cache.",
                                     formatter_class=RawTextHelpFormatter);

    parser.add_argument('files', type=str, nargs='*',
                        help='WTPERF configuration files to process');
    parser.add_argument('-o', '--ops', dest='ops',
                        action='append', nargs='+',
                        help='Operations to perform on the trace. Supported values \
                        are: correctness.');
    parser.add_argument('-s', '--start', dest='startString', default='',
                        help='Parsing begins after we the line containing \
                        this string');

    args = parser.parse_args();

    if (len(args.files) == 0):
        parser.print_help();
        sys.exit(1);

    if (args.ops == None):
        print("No operations suppied. Defaulting to " + supportedOps.CORRECTNESS);
        ops.append(supportedOps.CORRECTNESS);
    else:
        ops = args.ops;

    for f in args.files:
        parse_file(f, ops, args.startString);

if __name__ == '__main__':
    main()
