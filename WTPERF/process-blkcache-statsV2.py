#!/usr/bin/env python3

import argparse
import glob
import os
import os.path
import sys
from argparse import RawTextHelpFormatter
from pathlib import Path

outF = None;
headerNotDone = True;
statsName = "block-cache";

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

#
# Return True if the mtime of f1 is further into the future than that of f2
#
def younger(cwd, f1, f2):

    f1parts = f1.split(".");
    f2parts = f2.split(".");

    try:
        date1 = int(f1parts[1]);
        date2 = int(f2parts[1]);
        time1 = int(f1parts[2]);
        time2 = int(f2parts[2]);
    except:
        print(color.RED + color.BOLD + "Invalid name format " + f1 + " or " + f2);
        return False;

    if (date1 > date2):
        return True;
    if (date1 < date2):
        return False;

    if (time1 > time2):
        return True;
    else:
        return False;

def getMostRecentFile(files):

    filteredFiles = [];

    for f in files:
        if ((not f.startswith("WiredTigerStat")) or f.endswith(".txt")):
            continue;
        else:
            filteredFiles.append(f);

    cwd = os.path.abspath(os.curdir);
    print(cwd);

    filteredFiles.sort(key=lambda fn: os.path.getmtime(os.path.join(cwd, fn)))

    # We now have filtered and sorted files. We need to get the most recent file,
    # but it's not enough to get the one at the bottom of the list. We could have
    # two stats file with identical ctimes and mtimes, but one would be older
    # than the other. In this case, we must break times based on file names.
    #

    for i in range(len(filteredFiles) - 1):
        print(str(i));
        print(filteredFiles[i]);
        print(filteredFiles[i+1]);
        if (younger(cwd, filteredFiles[i], filteredFiles[i+1])):
            tmp = filteredFiles[i+1];
            filteredFiles[i+1] = filteredFiles[i];
            filteredFiles[i] = tmp;

    print("mrf is " + filteredFiles[len(filteredFiles) - 1]);
    return filteredFiles[len(filteredFiles) - 1];

def extractBenchmarkName(dirname):

    nameParts = dirname.split("/");

    name = nameParts[len(nameParts) - 1];
    nameParts2 = name.split(".");

    print(nameParts2[0]);

    return nameParts2[0];

def parseDir(d, outF):

    global statsName;
    global headerNotDone;
    idx = 0;

    topdir = os.path.abspath(os.curdir);
    os.chdir(d);

    statsFiles = list(filter(os.path.isfile, os.listdir()));

    mrf = getMostRecentFile(statsFiles);
    os.system("grep '^{' " + mrf + " | jq '.' > " + mrf + ".txt");

    # Read the lines in the file in reverse order to find the latest
    # block of the desired statistics.
    #
    f = open(mrf + ".txt")
    lines = f.readlines();

    idx = len(lines) - 1;
    while idx > 0:
        if (statsName in lines[idx]):
            break;
        idx = idx - 1;

    # If we have not yet created the output file header, do this now.
    if (headerNotDone):
        writeHeader(outF, lines, idx);

    # Extract the benchmark name from the directory name.
    # Each directory is for a different benchmark instance.
    #
    outF.write(extractBenchmarkName(d) + ",");

    # If the index idx is not zero, we found the desired statistics block.
    # Read forward to parse all the stats within that block.
    #
    for i in range(idx, len(lines)):
        if ("}" in lines[i]):
            break;
        words = lines[i].split(":");
        outF.write(words[1].strip().lstrip('{'));

    outF.write("\n");
    os.chdir(topdir);

#
# The header of the output csv file contains the names of the stats
# that we want to extract.
#
def writeHeader(outF, lines, idx):

    global headerNotDone;

    outF.write(",");

    for i in range(idx, len(lines)):
        if ("}" in lines[i]):
            break;
        words = lines[i].split(":");
        outF.write(words[0].strip().strip('"') + ",");

    outF.write("\n");
    headerNotDone = False;

def main():

    parser = argparse.ArgumentParser(description=
                                     "Parse requested wtperf stats and "
                                     "print them in the CSV format.",
                                     formatter_class=RawTextHelpFormatter);

    parser.add_argument('dirs', type=str, nargs='*',
                        help='Stats directories to process');

    parser.add_argument('-o', '--outputFile', dest='outputFile',
                                     default='wtperf-stats.csv',
                                     help='Output file name');

    args = parser.parse_args();

    if (len(args.dirs) == 0):
        parser.print_help();
        sys.exit(1);

    try:
        outF = open(args.outputFile, "w+");
    except:
        print(color.BOLD + color.RED + "Could not open " + args.outputFile + color.END);
        sys.exit(1);

    for d in args.dirs:
        parseDir(d, outF);

if __name__ == '__main__':
    main()
