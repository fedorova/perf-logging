#!/usr/bin/python -tt

import sys
import argparse

maxStretchLength = 0;
numFiles = 0;
timeKeyedRecords = {};

def parse_file(fname):

    global timeKeyedRecords;
    print "Parsing file " + fname;

    try:
        logFile = open(fname, "r");
    except:
        print "Could not open file " + fname;
        return;

    for line in logFile:
        words = line.split(" ");
        thread = 0;
        time = 0;
        event = "";

        if(len(words) < 4):
            continue;

        if(words[0] == "-->" or words[0] == "<--"):
            time = long(words[3]);
            timeKeyedRecords[time] = line;
        else:
            continue;

def find_overlapping_intervals():

    global maxStretchLength;
    global numFiles;
    global timeKeyedRecords;
    stretch = [];

    # Find all stretches of records where we have a sequence
    # of function enter records (marked with -->) of length
    # numFiles without an intervening function exit record.
    # Every such a sequence is an overlapping interval.
    for key, record in sorted(timeKeyedRecords.items()):

        words = record.split(" ");

        if(words[0] == "-->"):
            stretch.append(record);
        else:
            if(len(stretch) == numFiles):
                print("--------------");
                for i in range(len(stretch)) :
                    print(stretch[i]);

            if(len(stretch) > maxStretchLength):
                maxStretchLength = len(stretch);
            stretch = [];


def main():

    global maxStretchLength;
    global numFiles;

    parser = argparse.ArgumentParser(description=
                                     'Process performance log files');
    parser.add_argument('files', type=str, nargs='+',
                        help='log files to process');

    args = parser.parse_args();
    print args.files;

    for fname in args.files:
        parse_file(fname);
        numFiles = numFiles + 1;

    find_overlapping_intervals();
    print("Maximium overlapping intervals was " + str(maxStretchLength));

if __name__ == '__main__':
    main()
