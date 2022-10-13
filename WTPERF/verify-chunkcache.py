#!/usr/bin/env python3

import argparse
import os
import os.path
import sys
import traceback
from argparse import RawTextHelpFormatter


# Globals
#
# The chunk cache is a dictionary of dictionaries. One dictionary per object.
# An object is a file-id combination.
# A per-file dictionary contains chunks, keyed by their offsets.
#
chunkCacheAllFiles = {};
lastAllocatedChunkOffset = int(-1);
lastAllocatedChunkSize = int(-1);
lastMissedOffset = int(-1);

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

def process_alloc(cache, offset, size):

    global lastAllocatedChunkOffset;
    global lastAllocatedChunkSize;
    global lastMissedOffset;

    if (offset != lastMissedOffset):
        print(color.BOLD + color.RED + "Mismatch: allocating for offset " + str(offset) + \
                  ", but last missed offset was " + str(lastMissedOffset));

    lastAllocatedChunkOffset = offset;
    lastAllocatedChunkSize = size;
    print(color.BOLD + color.PURPLE + "Allocated offset=" + str(offset) + ", size=" + str(size) + color.END);

def process_check(cache, offset, size):

    global lastMissedOffset;

    if offset in cache:
        return;

    for cachedOffset in sorted(cache.keys()):
        cachedSize = cache[cachedOffset];
        if (cachedOffset < offset and (cachedOffset + cachedSize) > offset):
            return;

    lastMissedOffset = offset;
    print(color.BOLD + color.PURPLE + "Not found: offset=" + str(offset) + ", size=" + str(size) + color.END);


#
# This is a bit tricky. We are inserting lastAllocatedChunkOffset and lastAllocatedChunkSize.
# The offset and size parameters passed to the function indicate the place where we are inserting
# the last allocated chunk.
#
def process_insert(op, cache, offset, size):

    global lastAllocatedChunkOffset;
    global lastAllocatedChunkSize;

    if lastAllocatedChunkOffset in cache:
        print(color.BOLD + color.RED + "Offset " + str(lastAllocatedChunkOffset) + "already in cache.\n" + color.END);
        return;

    if (op == "insert" and len(cache) > 0):
        print(color.BOLD + color.RED + "insert first into a non-empty cache" + color.END);
        raise Exception("Index mismatch");

    cache[lastAllocatedChunkOffset] = lastAllocatedChunkSize;

    sortedKeys = sorted(cache.keys());
    print("Index of " + str(lastAllocatedChunkOffset) + " is " + str(sortedKeys.index(lastAllocatedChunkOffset)));

    insertedAtIndex = sortedKeys.index(lastAllocatedChunkOffset);

    if (offset == 0 and size == 0 and insertedAtIndex != 0):
        print(color.BOLD + color.RED + "insert-first: Mismatch between expected and allocated index. " + color.END);
        raise Exception("Index mismatch");

    if (op == "insert-before"):
        nextOffset = sortedKeys[insertedAtIndex + 1];
        if (lastAllocatedChunkOffset >= nextOffset):
            print(color.BOLD + color.RED + "insert-before: Mismatch between expected and allocated index. " + color.END);
            raise Exception("Index mismatch");
    elif (op == "insert-after"):
        previousOffset = sortedKeys[insertedAtIndex-1];
        if (lastAllocatedChunkOffset <= previousOffset):
            print(color.BOLD + color.RED + "insert-after: Mismatch between expected and allocated index. " + color.END);
            raise Exception("Index mismatch");
    return;

def get_tokens(line):

    opAndElse = line.split(":");

    if (len(opAndElse) < 2):
        print(color.BOLD + color.RED + "Could not parse:\n" + line + color.END);
        traceback.print_exc();
        raise Exception("Split 1");

    op = opAndElse[0];

    opParams = opAndElse[1].strip().split(",");
    if (len(opParams) < 3):
        print(color.BOLD + color.RED + "Could not parse:\n" + line + color.END);
        traceback.print_exc();
        raise Exception("Split 2");

    fid = opParams[0].strip();

    offsetWords = opParams[1].strip().split("=");
    if (len(offsetWords) < 2 or not (offsetWords[0] == "offset")):
        print(color.BOLD + color.RED + "Could not parse:\n" + line + color.END);
        traceback.print_exc();
        raise Exception("Split 3");
    offset = offsetWords[1];

    sizeWords = opParams[2].strip().split("=");
    if (len(sizeWords) < 2 or not (sizeWords[0] == "size")):
        print(color.BOLD + color.RED + "Could not parse:\n" + line + color.END);
        traceback.print_exc();
        raise Exception("Split 4");
    size = sizeWords[1];

    return op, fid, int(offset), int(size);

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
        process_insert(op, chunkCache, offset, size);

def process_line(line):

    if line.startswith(cacheOps.CHECK) or line.startswith(cacheOps.ALLOC) or \
        line.startswith(cacheOps.INSERT):
        try:
            op, fid, offset, size = get_tokens(line);
            print(op + " " + fid + " " + str(offset) + " " + str(size));
            process_cache_op(op, fid, offset, size);
        except:
            print(color.BOLD + color.RED + "Could not parse:\n" + line + color.END);
            traceback.print_exc();
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
