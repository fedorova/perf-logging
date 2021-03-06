#!/usr/bin/env python3

import argparse
import os
import os.path
import sys
from argparse import RawTextHelpFormatter

# Globals
#
blockCache = {};

totalFS_ReadLatencySamples = 0;
totalFS_WriteLatencySamples = 0;
totalMemoryReadLatencySamples = 0;
totalMemoryWriteLatencySamples = 0;

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
    LATENCY = 'latency'

class cacheOps:
    INSERT = 'inserted'
    FOUND  = ' found '
    NOTFOUND = 'not found'
    REMOVED = 'removed'
    MEMORY_READ_LATENCY = 'memory read'
    FS_READ_LATENCY = 'file system read'
    MEMORY_WRITE_LATENCY = 'memory write'
    FS_WRITE_LATENCY = 'file system write'

class blockStatus:
    UNCACHED = 0
    CACHED = 1

class Block:
    def __init__(self, fname, offset, size, checksum, line):
        self.checksum = checksum.rstrip(',');
        self.fname = fname.rstrip(',');
        self.offset = offset.rstrip(',');
        self.size = size.rstrip(',');
        self.line = line; # line in trace file during insert
        self.status = blockStatus.UNCACHED;
        #
        self.hits = 0;
        self.misses = 0;
        self.fileSystemReadLatencies = [];
        self.memoryAccessReadLatencies = [];
        self.fileSystemWriteLatencies = [];
        self.memoryAccessWriteLatencies = [];
        self.averageReadFSL = 0.0;
        self.averageReadML = 0.0;
        self.averageWriteFSL = 0.0;
        self.averageWriteML = 0.0;

    def getAverageReadFSL(self):
        return self.averageReadFSL;

    def getAverageReadML(self):
        return self.averageReadML;

    def getAverageWriteFSL(self):
        return self.averageWriteFSL;

    def getAverageWriteML(self):
        return self.averageWriteML;

    def getFSLReadSamples(self):
        return len(self.fileSystemReadLatencies);

    def getFSLWriteSamples(self):
        return len(self.fileSystemWriteLatencies);

    def getMLReadSamples(self):
        return len(self.memoryAccessReadLatencies);

    def getMLWriteSamples(self):
        return len(self.memoryAccessWriteLatencies);

    def computeAverageLatencies(self):

        sumFSL = 0;
        for fsl in self.fileSystemReadLatencies:
            sumFSL += int(fsl);
        if (len(self.fileSystemReadLatencies) > 0):
            self.averageReadFSL = sumFSL/len(self.fileSystemReadLatencies);
        else:
            self.averageReadFSL = 0;

        sumFSL = 0;
        for fsl in self.fileSystemWriteLatencies:
            sumFSL += int(fsl);
        if (len(self.fileSystemWriteLatencies) > 0):
            self.averageWriteFSL = sumFSL/len(self.fileSystemWriteLatencies);
        else:
            self.averageWriteFSL = 0;

        sumML = 0;
        for ml in self.memoryAccessReadLatencies:
            sumML += int(ml);
        if (len(self.memoryAccessReadLatencies) > 0):
            self.averageReadML = sumML/len(self.memoryAccessReadLatencies);
        else:
            self.averageReadML = 0;

        sumML = 0;
        for ml in self.memoryAccessWriteLatencies:
            sumML += int(ml);
        if (len(self.memoryAccessWriteLatencies) > 0):
            self.averageWriteML = sumML/len(self.memoryAccessWriteLatencies);
        else:
            self.averageWriteML = 0;

    def printBlock(self, printColor):
        print("\t" + printColor + self.fname + ", off=" + str(self.offset) +
              ", size=" + str(self.size) + ", checksum=" + str(self.checksum) +
              ", line=" + str(self.line) +
              ", status=" + str(self.status) + ", hits=" + str(self.hits) +
              ", misses=" + str(self.misses));

        self.computeAverageLatencies();

        print("\tFile system read latencies:");
        for fsl in self.fileSystemReadLatencies:
            print("\t\t" + str(fsl));
        print("\t\tAVERAGE READ FSL: " + str(int(self.averageReadFSL)));

        print("\tFile system write latencies:");
        for fsl in self.fileSystemWriteLatencies:
            print("\t\t" + str(fsl));
        print("\t\tAVERAGE WRITE FSL: " + str(int(self.averageWriteFSL)));

        print("\tMemory read latencies:");
        for ml in self.memoryAccessReadLatencies:
            print("\t\t" + str(ml));
        print("\t\tAVERAGE READ ML: " + str(int(self.averageReadML)));

        print("\tMemory write latencies:");
        for ml in self.memoryAccessWriteLatencies:
            print("\t\t" + str(ml));
        print("\t\tAVERAGE WRITE ML: " + str(int(self.averageWriteML)));

        print(color.END);

    def __eq__(self, other):
        return other and self.fname == other.fname and self.offset == other.offset \
            and self.size == other.size and self.checksum == other.checksum

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.fname, self.offset, self.size, self.checksum))

def printCache():

    global blockCache;
    global totalFS_ReadLatencySamples;
    global totalFS_WriteLatencySamples;
    global totalMemoryReadLatencySamples;
    global totalMemoryWriteLatencySamples;

    accumAvgReadFSL = 0.0;
    accumAvgWriteFSL = 0.0;
    accumAvgReadML  = 0.0;
    accumAvgWriteML  = 0.0;

    for hashV, block in blockCache.items():
        block.printBlock(color.PURPLE);
        if (totalFS_ReadLatencySamples > 0):
            accumAvgReadFSL += block.getAverageReadFSL() * \
                float(block.getFSLReadSamples()) / float(totalFS_ReadLatencySamples);
        if (totalFS_WriteLatencySamples > 0):
            accumAvgWriteFSL += block.getAverageWriteFSL() * \
                float(block.getFSLWriteSamples()) / float(totalFS_WriteLatencySamples);
        if (totalMemoryReadLatencySamples > 0):
            accumAvgReadML += block.getAverageReadML() * \
                float(block.getMLReadSamples()) / float(totalMemoryReadLatencySamples);
        if (totalMemoryWriteLatencySamples > 0):
            accumAvgWriteML += block.getAverageWriteML() * \
                float(block.getMLWriteSamples()) / float(totalMemoryWriteLatencySamples);

    print(color.BOLD + color.PURPLE);
    print("\tCache-wide AVERAGE Read FSL: " + str(int(accumAvgReadFSL)));
    print("\tCache-wide AVERAGE Write FSL: " + str(int(accumAvgWriteFSL)));
    print("\tCache-wide AVERAGE Read ML: " + str(int(accumAvgReadML)));
    print("\tCache-wide AVERAGE Write ML: " + str(int(accumAvgWriteML)));
    print(color.END);

def blockCached(block):

    global blockCache;

    if (hash(block) in blockCache):
        if (blockCache[hash(block)].status == blockStatus.CACHED):
            return True;
        else:
            return False;
    else:
        return False;

def insertBlock(newBlock):

    global blockCache;

    if (hash(newBlock) not in blockCache):
        blockCache[hash(newBlock)] = newBlock;
    blockCache[hash(newBlock)].status = blockStatus.CACHED;

def removeBlock(block):

    blockCache[hash(block)].status = blockStatus.UNCACHED;

# Add the block to the cache structure if it's not there, with the
# UNCACHED status, so that we can keep track of misses and latency.
#
def addToCacheStructure(block):

    if (hash(block) not in blockCache):
        if (block.status == blockStatus.CACHED):
            printError("Cached block not in cache structure.", block, linenum);
            return;
        blockCache[hash(block)] = block;

def incrementStats(block, stat):

    global blockCache;

    addToCacheStructure(block);

    blockRef = blockCache[hash(block)];

    if (stat == "misses"):
        blockRef.misses += 1;
    elif (stat == "hits"):
        blockRef.hits += 1;

def printVerbose(message, block, line):

    print(color.BLUE + "line: " + str(line) + " " + message + color.END);
    block.printBlock(color.BLUE);

def printError(message, block, line):

    print(color.RED + color.BOLD + "line: " + str(line) +
          " ERROR: " + message + color.END);
    block.printBlock(color.RED + color.BOLD);

def getLatency(line):

    words = line.strip().split(" ");

    for word in words:
        if ("latency=" in word):
            lat_words = word.strip().split('=');
            if (len(lat_words) < 2):
                return 0;
            else:
                return lat_words[1];

def processCorrectness(line, lineNum):

    global blockCache;
    checksum = 0;
    fname = "";
    offset = 0;
    size = 0;

    if (not "[WT_VERB_BLKCACHE]" in line):
        return None;

    if ("initialized" in line):
        print(color.BOLD + color.BLUE +
              "The following command will initialize the block cache. \n" +
              "Block cache currently contains " + str(len(blockCache)) + " blocks." +
              color.END);
        print(line);
        blockCache = {};
        return None;
    if ("destroy" in line):
        print(color.BOLD + color.BLUE + "Cache with " + str(len(blockCache)) +
              " blocks destroyed." + color.END);
        print(line);
        return None;

    words = line.strip().split(" ");

    for word in words:
        if ("file:" in word):
            fname = word.split(":")[1];
        if ("offset=" in word):
            offset = word.split("=")[1];
        if ("size=" in word):
            size = word.split("=")[1];
        if ("checksum=" in word):
            checksum = word.split("=")[1];

    if (fname == "" or offset == 0 or size == 0):
        print(color.RED + "Invalid block parameters:\n\t" + line + color.END);
        return None;

    newBlock = Block(fname, offset, size, checksum, lineNum);

    if (cacheOps.INSERT in line):
        # printVerbose("Inserting new block.", newBlock, lineNum);
        if (blockCached(newBlock)):
            printError("Block already cached.", blockCache[hash(newBlock)], lineNum);
        else:
            insertBlock(newBlock);

    elif (cacheOps.NOTFOUND in line):
        if (blockCached(newBlock)):
            printError("Block expected to be in cache, but NOT found.",
                       blockCache[hash(newBlock)], lineNum);
        else:
            incrementStats(newBlock, "misses");
    elif (cacheOps.FOUND in line):
        if (not blockCached(newBlock)):
            printError("Block NOT expected to be in cache, but found.",
                       newBlock, lineNum);
        else:
            incrementStats(newBlock, "hits");
    elif (cacheOps.REMOVED in line):
        if (not blockCached(newBlock)):
            printError("Block to be removed expected in cache, but NOT found:" +
                       newBlock, lineNum);
        else:
            removeBlock(newBlock);

    return newBlock;

#
# The block argument is the block that was parsed by the function responsible
# for tracking correctness. It may or may not be cached.
#
def processLatency(block, line, lineNum):

    global blockCache;
    global totalFS_ReadLatencySamples;
    global totalFS_WriteLatencySamples;
    global totalMemoryReadLatencySamples;
    global totalMemoryWriteLatencySamples;

    addToCacheStructure(block);

    blockRef = blockCache[hash(block)];

    if (cacheOps.FS_READ_LATENCY in line):
        latency = getLatency(line);
        blockRef.fileSystemReadLatencies.append(latency);
        totalFS_ReadLatencySamples += 1;
    elif (cacheOps.FS_WRITE_LATENCY in line):
        latency = getLatency(line);
        blockRef.fileSystemWriteLatencies.append(latency);
        totalFS_WriteLatencySamples += 1;
    elif (cacheOps.MEMORY_READ_LATENCY in line):
        latency = getLatency(line);
        blockRef.memoryAccessReadLatencies.append(latency);
        totalMemoryReadLatencySamples += 1;
    elif (cacheOps.MEMORY_WRITE_LATENCY in line):
        latency = getLatency(line);
        blockRef.memoryAccessWriteLatencies.append(latency);
        totalMemoryWriteLatencySamples += 1;

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
        i += 1;
        if (not startStringSeen):
            if (startString in line):
                startStringSeen = True;
                print("Found " + startString + " on line " + str(i));
            else:
                continue;

        block = processCorrectness(line, i);
        if (block is None):
            continue;

        for op in ops:
            if (op == supportedOps.LATENCY):
                processLatency(block, line, i);

    printCache();

def main():

    ops = [];

    parser = argparse.ArgumentParser(description=
                                     "Parse wt_verbose traces to collect information "
                                     "about the behaviour of the block cache.",
                                     formatter_class=RawTextHelpFormatter);

    parser.add_argument('files', type=str, nargs='*',
                        help='Trace files to process');
    parser.add_argument('-o', '--ops', dest='ops',
                        action='append', nargs='+',
                        help='Operations to perform on the trace. Supported values \
                        are: correctness, latency. Correctness processing is always \
                        performed. Default: all operations.');
    parser.add_argument('-s', '--start', dest='startString', default='',
                        help='Parsing begins after we the line containing \
                        this string');

    args = parser.parse_args();

    if (len(args.files) == 0):
        parser.print_help();
        sys.exit(1);

    if (args.ops == None):
        print("No operations supplied. Defaulting to all:");

        members = [attr for attr in dir(supportedOps) \
                   if not callable(getattr(supportedOps, attr)) \
                   and not attr.startswith("__")]

        for var in members:
            print("\t " + getattr(supportedOps, var));
            ops.append(getattr(supportedOps,var));
    else:
        ops = args.ops;

    for f in args.files:
        parse_file(f, ops, args.startString);

if __name__ == '__main__':
    main()
