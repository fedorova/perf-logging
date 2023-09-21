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


def parseAddr(addr):

    addrComponents = addr.split(" ");
    offset = addrComponents[1].split("-")[0];
    size = addrComponents[2].strip(",");

    return offset, size;

def parseTime(time):
    timeComponents = time.split(":");
    return int(timeComponents[0]) * 1000000 + int(timeComponents[1]);


#
# Parse lines that look like this:
#
# [1695171718:241987][73439:0x1121b2e00], file:test.wt, WT_CONNECTION.close:
#         [WT_VERB_CACHE_TRACE][DEBUG_1]: cache-hit 0x7fbdf8271800
#         addr [0: 1200701440-1200730112, 28672, 2351440508] type leaf read_gen 19147
#
# The first item in square brackets is time: seconds and microseconds.
# The addr structure contains object ID, the range of offsets spanned by the item, its
# size and the checksum.
#
def process_line(line):
    #
    # This matches various characters between square brackets
    # and puts all the results in a list.
    #
    res = re.findall(r"\[([A-Za-z0-9_\-:, ]+)\]", line);

    # Discard unwanted debug messages
    if (res[2] != "WT_VERB_CACHE_TRACE"):
        return;

    # The time consists of seconds and microseconds. Convert to microseconds.
    time = parseTime(res[0]);
    offset, size = parseAddr(res[4]);

    #print("Time is: ");
    #print("\t" +  res[0] + " " + str(time));
    #print("addr is: ");
    #print("\t" + res[4] + " offset = " + offset + ", size = " + size);

    print(str(time) + "," + str(offset) + "," + str(size));

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
                                     "Convert the WiredTiger cache trace to CSV for libcachesim.",
                                     formatter_class=RawTextHelpFormatter);
    parser.add_argument('files', type=str, nargs='*',
                        help='Trace file to process');

    args = parser.parse_args();

    if (len(args.files) == 0):
        parser.print_help();
        sys.exit(1);

    for f in args.files:
        parse_file(f);


if __name__ == '__main__':
    main()
