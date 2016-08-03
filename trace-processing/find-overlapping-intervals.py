#!/usr/bin/python -tt

import sys
import argparse
import os

timeKeyedRecords = {};
runLengthForFilter = {};

#
# This is a convenience function, so we can print a record with a nicely
# formatted timestamp.
#
def printRecord(record, minTimestamp):

    words = record.split(" ");

    if(len(words) < 4):
        print("Invalid record " + record);
        return;

    print(words[1] + " " + words[2] + " " +
          '{:,}'.format(int(words[3]) - minTimestamp));

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

    mergedIntervals = {};
    global runLengthForFilter;
    global timeKeyedRecords;
    interval = [];

    # Check if there are environment variables overriding the
    # default setting for the acceptable run length for each filter.
    # The default is the number of files matching that filter
    for filter_name in timeKeyedRecords.keys():
        if(os.environ.get(filter_name) is not None):
            try:
                runLengthForFilter[filter_name] = int(os.environ[filter_name]);
                print("Using run length " + str(runLengthForFilter[filter_name])
                      + " for filter " + filter_name);
            except:
                print("Invalid run length specified in variable [" + filter_name
                      + "]: " + os.environ[filter_name]
                      + ". Defaulting to " +
                      + str(runLengthForFilter[filter_name]) + ".");

    # Find all intervales of records where we have a sequence
    # of function enter records (marked with -->) of length
    # runLength without an intervening function exit record.
    # Every such a sequence is an overlapping interval.
    #
    # When we find such an interval for a given filter name,
    # add it to the mergedIntervals dictionary, which will contain the
    # intervals for all the filters, keyed by the timestamp marking when
    # the interval begins. At the end we will print this dictionary.
    #
    for filter_name, dictionary in timeKeyedRecords.iteritems():
        print("Processing dictionary " +
              filter_name + " of " + str(len(dictionary)) + " items.");

        intervalStartTime = 0;

        for key, record in sorted(dictionary.items()):

            words = record.split(" ");

            if(words[0] == "-->"):
                # If we have no records in the interval, we are
                # just starting the new interval, so let's remember the time
                # when the interval has begun. It will be used as the key
                # when we add the interval begins.
                if(len(interval) == 0):
                    try:
                        intervalStartTime = int(words[3]);
                    except:
                        print("Could not parse time stamp in this record: " +
                              record);
                        continue;

                interval.append(record);

            elif(words[0] == "<--"):   # Possibly the end of the interval
                if(len(interval) == runLengthForFilter[filter_name]):
                    mergedIntervals[intervalStartTime] = interval;

                interval = [];
            else:
                print("Unexpected record type: " + record);

    # Print the mergedIntervals dictionary.
    minTimestamp = min(mergedIntervals, key=int);
    for timestamp, interval in sorted(mergedIntervals.items()):
        print('{:,}'.format(timestamp - minTimestamp)
              + " ------------------------------");
        for record in interval:
            printRecord(record, minTimestamp);
        print("------------------------------------------------");

def main():

    parser = argparse.ArgumentParser(description=
                                     'Process performance log files');
    parser.add_argument('files', type=str, nargs='+',
                        help='log files to process');

    args = parser.parse_args();
    print args.files;

    for fname in args.files:
        parse_file(fname);

    find_overlapping_intervals();

if __name__ == '__main__':
    main()
