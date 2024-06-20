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

def process_cachesim_trace():

    blocksCached = {};
    maxBytesCached = 0;
    totalBytesCached = 0;

    address = 0;
    size = 0;
    opr = 0;

    for line in sys.stdin:
        fields = line.strip().split(',')
        if len(fields) < 2:  # Ensure there are at least two fields
            ERROR("Fewer than two fields");

        address = int(fields[1]);
        size = int(fields[2]);
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
            del blocksCached[address];

    print(f"Max bytes cached {maxBytesCached}");

def main():

    process_cachesim_trace();

if __name__ == '__main__':
    main()
