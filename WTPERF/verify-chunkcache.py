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
allocatedChunks = {};

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
    ALLOC = 'allocate'
    EVICT  = 'evict'
    GET = 'get'
    INSERT = 'insert'
    REMOVE = 'remove'

def process_alloc(cache, offset, size):

    global allocatedChunks;

    if offset in allocatedChunks:
        print(color.BOLD + color.RED + "Double allocation for offset " + str(offset) + color.END);
        sys.exit(-1);

    if offset in cache:
        print(color.BOLD + color.RED + "Allocated offset " + str(offset) + " already cached" \
              + color.END);
        sys.exit(-1);

    allocatedChunks[offset] = size;

def process_evict(cache, offset, size):

    if offset not in cache:
        print(color.BOLD + color.RED + "Evicted offset " + str(offset) + " not in cache " +\
              color.END);
        sys.exit(-1);

    del cache[offset];


def process_get(cache, offset, size):

    beginningFound = False;
    bytesFound = 0;

    for chunkOffset in sorted(cache.keys()):
        chunkSize = cache[chunkOffset];
        # Block is entirely in a chunk
        if (chunkOffset <= offset and (chunkOffset+chunkSize >= offset+size)):
            return;
        # Block begins in the chunk
        if (chunkOffset <= offset and (offset <  chunkOffset+chunkSize) and \
            (offset+size > chunkOffset+chunkSize)):
            print(color.BOLD + color.PURPLE + "BEGINS in CHUNK: " + \
                  "offset=" + str(offset) + ", size=" + str(size) + \
                  ", chunk offset=" + str(chunkOffset) + ", chunk_size=" + str(chunkSize) +\
                  color.END);
            bytesFound = (chunkOffset+chunkSize - offset);
            offset += bytesFound;
            size -= bytesFound;
            beginningFound = True;
        if (chunkOffset > offset and (chunkOffset+chunkSize >= offset+size) and \
            chunkOffset < (offset + size)):
            print(color.BOLD + color.PURPLE + "ENDS in CHUNK: " + \
                  "offset=" + str(offset) + ", size=" + str(size) + \
                  ", chunk offset=" + str(chunkOffset) + ", chunk_size=" + str(chunkSize) +\
                  color.END);
            if (not beginningFound):
                break;
        if (chunkOffset > offset + size):
            break;

    print(color.BOLD + color.PURPLE + "Not found: offset=" + str(offset) + ", size=" + str(size) + color.END);

#
# Check if the inserted chunk had been allocated and is not already cached.
#
def process_insert(cache, offset, size):

    global allocatedChunks;

    if offset not in allocatedChunks:
         print(color.BOLD + color.RED + "Inserted chunk at offset " + str(offset) + \
           " has NOT been allocated " + color.END);
         sys.exit(-1);

    del allocatedChunks[offset];

    if offset in cache:
        print(color.BOLD + color.RED + "Inserted chunk at offset " + str(offset) + \
           " is already cached " + color.END);
        sys.exit(-1);

    cache[offset] = size;


def process_remove(cache, offset, size):

    if offset not in cache:
        print(color.BOLD + color.RED + "Removed offset " + str(offset) + " not in cache " +\
              color.END);

    del cache[offset];

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

    if (op == cacheOps.ALLOC):
        process_alloc(chunkCache, offset, size);
    elif (op == cacheOps.EVICT):
        process_evict(chunkCache, offset, size);
    elif (op == cacheOps.GET):
        process_get(chunkCache, offset, size);
    elif (op == cacheOps.INSERT):
        process_insert(chunkCache, offset, size);
    elif (op == cacheOps.REMOVE):
        process_remove(chunkCache, offset, size);

def process_line(line):

    global allocatedChunks;
    global chunkCacheAllFiles;

    if ("configured cache" in line):
        allocatedChunks.clear();
        chunkCacheAllFiles.clear();
        print("Clearing the caches...");

    if line.startswith(cacheOps.ALLOC + ":") or line.startswith(cacheOps.EVICT + ":") or \
      line.startswith(cacheOps.GET + ":") or line.startswith(cacheOps.INSERT + ":") or \
      line.startswith(cacheOps.REMOVE + ":"):
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
