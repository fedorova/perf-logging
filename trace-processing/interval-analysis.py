#!/usr/bin/python -tt

import sys
import argparse
import re

giantDict = {}

def parse_file(fname):

    print "Parsing file " + fname;

    try:
        logFile = open(fname, "r");
    except:
        print "Could not open file " + fname;
        return;

    for line in logFile:

        words = line.split(" ");

        if(len(words) < 4):
           continue;

        try:
            time = long(words[3]);
        except ValueError:
            print "Could not parse: " + line;
            continue;

        giantDict[time] = line;


def aggregate(pattern, intervalLength):

    numMatchesThisInterval = 0;
    currentIntervalBegin = 0;
    lineBegin = 0;
    lineNumber = 0;

    regexp = re.compile(pattern);

    for key, value in sorted(giantDict.iteritems()):

        time = key;
        line = value;
        lineNumber = lineNumber + 1;

        # See if we need to reset the interval
        if(currentIntervalBegin == 0):
            currentIntervalBegin = time;
            lineBegin = lineNumber;

        # See if this record matches the pattern
        match = regexp.search(line)
        if(match is not None):
            numMatchesThisInterval = numMatchesThisInterval + 1;

        # See if we need to end the current interval
        if((time - currentIntervalBegin) > intervalLength):
            print(str(lineBegin) + " " + str(currentIntervalBegin) + " - " +
                  str(time) + " : " + str(numMatchesThisInterval));
            numMatchesThisInterval = 0;
            currentIntervalBegin = 0;

def main():

    parser = argparse.ArgumentParser(description=
                                     'Process performance log files');
    parser.add_argument('files', type=str, nargs='+',
                        help='log files to process');
    parser.add_argument("-p", "--pattern", type=str, nargs=1,
                        help="string to match in a record");
    parser.add_argument("-t", "--time", type=int, nargs=1,
                        help="time interval when matches will be printed");

    args = parser.parse_args();
    print args.files;
    print("Pattern string is: "),
    print args.pattern;
    print("Time interval is: "),
    print args.time;

    for fname in args.files:
        parse_file(fname);

    aggregate(args.pattern[0], args.time[0]);

if __name__ == '__main__':
    main()
