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

class Object:
	def __init__(objectId, accessTime):
		self.objectID = objectId;
		self.accessTime = accessTime;
		self.cached = False;
		self.numTimesEvicted = 0;
		self.numAccesses = 0;
		self.objectId = 0;
		self.readGen = 0;

cachedObjects = {};

def parseAddr(addr):

    addrComponents = addr.split(" ");
    offset = addrComponents[1].split("-")[0];
    size = addrComponents[2].strip(",");

    return offset, size;

def parseTime(time):
    timeComponents = time.split(":");
    return int(timeComponents[0]) * 1000000 + int(timeComponents[1]);

def parseType(type):
    if (type == "intl"):
        return "0";
    else:
        return "1";

def getParentAddr(parent_page_ptr):
    #
    # Given a page pointer, return the on-disk address.
    #
    global pagePtrToAddr;

    if (parent_page_ptr in pagePtrToAddr):
        return pagePtrToAddr[parent_page_ptr];
    else:
        return 0;

def recordPageAddr(page_ptr, addr):
    #
    # We keep a mapping between the page pointer and the address,
    # so that given a parent page pointer we can find the corresponding
    # address.
    #
    global pagePtrToAddr;
    pagePtrToAddr[page_ptr] = addr;

#
# Parse lines that look like this:
#
# [1695171718:241987][73439:0x1121b2e00], file:test.wt, WT_CONNECTION.close:
#         [WT_VERB_CACHE_TRACE][DEBUG_1]: cache-hit 0x7fbdf8271800
#         addr [0: 1200701440-1200730112, 28672, 2351440508] type leaf read_gen 19147
#         parent_page 0x7fbdf8271800
#
# The first item in square brackets is time: seconds and microseconds.
# The addr structure contains object ID, the range of offsets spanned by the item, its
# size and the checksum.
#
def process_line(line, fileFilter, generic):

    i = 0;
    parent_addr = "0";
    parent_page = "0";
    read_gen = "0";
    type = "2";
    op_type = op.CACHE_ACCESS;

    # Split the line using space as the delimiter.
    fields = line.split(" ");

    # Special cases to skip debug messages we don't need.
    if ("WT_VERB_CACHE_TRACE" not in line):
        return;

    if ("evict-queue" in line):
        return;

    for i in range(0, len(fields)):
        if (fields[i].startswith("file:")):
            fileName = fields[i].split(":")[1].strip(",");
            if (fileName != fileFilter):
                return;
            break;
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

    # Find the other interesting fields.
    for i in range(i, len(fields)):
        if (fields[i].startswith("cache-") or fields[i].startswith("init-root")):
            recordPageAddr(fields[i+1], offset);
            if (fields[i] == "cache-hit" and "evict pass" in line):
                op_type = op.EVICT_LOOK;
        elif (fields[i] == "evict-add"):
            op_type = op.EVICT_ADD;
        elif (fields[i] == "evict"):
            op_type = op.EVICT;
        elif (fields[i] == "type"):
            type = parseType(fields[i+1]);
        elif (fields[i] == "read_gen"):
            read_gen = fields[i+1];
        elif (fields[i] == "parent_page"):
            parent_addr = getParentAddr(fields[i+1].strip());

    # For a generic cache simulator, we only care about access operations and only the
    # first three fields
    #
    if (generic):
        if (op_type ==  op.CACHE_ACCESS):
            print(str(time) + "," + str(offset) + "," + str(size));
        else:
            return;
    else:
        print(str(time) + "," + str(offset) + "," + str(size) + "," + str(type) + ","
            + str(read_gen) + "," + str(parent_addr) + "," + str(op_type));

def processWiredTigerLine(line):

	global cachedObjects;

	if ("WT_find" in line):
		

def parseWiredTigerTrace(fname):

    try:
        f = open(fname);
    except:
        print(color.BOLD + color.RED + "Could not open " + fname + color.END);
        sys.exit(1);

    for line in f.readlines():
		if ("WT_find" in line or "Removed" in line):
			processWiredTigerLine(line);

def main():

    parser = argparse.ArgumentParser(
		description= "Analyze WiredTiger cache trace in comparison with another algorithm");
                                     formatter_class=RawTextHelpFormatter);
    parser.add_argument('-w', dest='wtTrace', type=str, help='WiredTiger simulator output file');
	parser.add_argument('-o', dest='otherTrace', type=str,
						help='Simulator output file for the other algorithm');

    args = parser.parse_args();

    if (args.wtTrace is None or args.otherTrace is None):
        parser.print_help();
        sys.exit(1);

	parseWiredTigerTrace(args.wtTrace);
	parseOtherTrace(args.otherTrace);

if __name__ == '__main__':
    main()
