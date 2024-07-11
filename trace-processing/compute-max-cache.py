#!/usr/bin/env python3

import argparse
import os
import os.path
import re
import sys
import traceback
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

class op:
    CACHE_ACCESS = 0
    EVICT = 1
    EVICT_ADD = 2
    EVICT_LOOK = 3

def ERROR(msg):
    print(color.BOLD + color.RED + msg + color.END);
    sys.exit(1);


#
# The lines in the trace file look like this:
# 1720042798022668,13840396288,4096,0,0,13840461824,0
#
def process_cachesim_trace(fname):

    blocksCached = {};
    maxBytesCached = 0;
    totalBytesCached = 0;
    totalEvictions = 0;

    address = 0;
    readgen = 0;
    size = 0;
    opr = 0;

    try:
        f = open(fname);
    except:
        print(color.BOLD + color.RED + "Could not open " + fname + color.END);
        sys.exit(1);

    fname_parts = fname.split(".");
    readgenFname = fname_parts[0] + ".wt-native-readgens";

    try:
        readgenFile = open(readgenFname, "w");
    except:
        print(color.BOLD + color.RED + "Could not open " + readgenFname + color.END);
        sys.exit(1);

    for line in f.readlines():
        fields = line.strip().split(',')
        if len(fields) < 2:  # Ensure there are at least two fields
            ERROR("Fewer than two fields in line: \n" + line);

        address = int(fields[1]);
        size = int(fields[2]);
        readgen = int(fields[4]); 
        opr = int(fields[-1]);

        if (opr == op.CACHE_ACCESS):
            if (address in blocksCached):
                continue;
            blocksCached[address] = size;
            totalBytesCached += size;
            if (totalBytesCached > maxBytesCached):
                maxBytesCached = totalBytesCached;
        elif (opr == op.EVICT):
            totalBytesCached -= blocksCached[address];
            totalEvictions += 1;
            del blocksCached[address];
            readgenFile.write(f"{readgen}\n");

    print(f"Max bytes cached {maxBytesCached}");
    print(f"Total evictions {totalEvictions}");

def main():

    parser = argparse.ArgumentParser(description=
                                     "Compute stats of the cachesim trace",
                                     formatter_class=RawTextHelpFormatter);
    parser.add_argument('files', type=str, nargs='*',
                        help='WiredTiger libcachesim trace file.');

    args = parser.parse_args();

    if (len(args.files) == 0):
        parser.print_help();
        sys.exit(1);

    for f in args.files:
        process_cachesim_trace(f);

if __name__ == '__main__':
    main()
