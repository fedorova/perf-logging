#!/usr/bin/python -tt

import sys
import argparse

maxStretchLength = 0;
timeKeyedRecords = {};
runLengthForFilter = {};

def parse_file(fname):

    global runLengthForFilter;
    global timeKeyedRecords;
    print "Parsing file " + fname;

    # Find the last component of the file name after the "."
    # That is the name of the filter applied to the original
    # trace. Each filter name gets its own dictionary.
    words = fname.split(".");
    filter_name = words[len(words)-1];

    if filter_name not in timeKeyedRecords:
        timeKeyedRecords[filter_name] = {}
        runLengthForFilter[filter_name] = 0;
        print "Created dictionary for filter name: " + filter_name;

    try:
        logFile = open(fname, "r");
        runLengthForFilter[filter_name] = runLengthForFilter[filter_name] + 1;
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
            timeKeyedRecords[filter_name][time] = line;
        else:
            continue;

def find_overlapping_intervals():

    global maxStretchLength;
    global runLengthForFilter;
    global timeKeyedRecords;
    stretch = [];

    # Check if there are environment variables overriding the
    # default setting for the acceptable run length for each filter.
    # The default is the number of files matching that filter
    for filter_name, dictionary in timeKeyedRecords.keys():
        if(os.environ[filter_name] not None):
            runLengthForFilter[filter_name] = int(os.environ[filter_name]);
            print("Detected run lenght " + str(runLengthForFilter[filter_name])
                  + " for filter " + filter_name);

    # Find all stretches of records where we have a sequence
    # of function enter records (marked with -->) of length
    # runLength without an intervening function exit record.
    # Every such a sequence is an overlapping interval.
    #
    for filter_name, dictionary in timeKeyedRecords.items():
        print("Processing dictionary " +
              filter_name + " of " + str(len(dictionary)) + " items.");

        for key, record in sorted(dictionary.items()):

            words = record.split(" ");

            if(words[0] == "-->"):
                stretch.append(record);
            else:
                if(len(stretch) == runLengthForFilter[filter_name]):
                    print("--------------");
                    for i in range(len(stretch)) :
                        print(stretch[i]);

                if(len(stretch) > maxStretchLength):
                    maxStretchLength = len(stretch);

                stretch = [];


def main():

    global maxStretchLength;

    parser = argparse.ArgumentParser(description=
                                     'Process performance log files');
    parser.add_argument('files', type=str, nargs='+',
                        help='log files to process');

    args = parser.parse_args();
    print args.files;

    for fname in args.files:
        parse_file(fname);

    find_overlapping_intervals();
    print("Maximium overlapping intervals was " + str(maxStretchLength));

if __name__ == '__main__':
    main()
