#!/usr/bin/python -tt

# This script is really a place to create one-off scripts to filter data in
# ways that can't be done easily with other command line tools.
#

import sys
import argparse

def parse_file(fname, parent, child):

    parentLine = "";
    childOn = False;
    printedParentLine = False;
    outputFileName = fname + "." + parent + "." + child;
    numLinesChildThreshold = 2;

    print "Parsing file " + fname;
    print "Will write to " + outputFileName;

    try:
        logFile = open(fname, "r");
    except:
        print "Could not open file " + fname;
        return;

    try:
        outputFile = open(outputFileName, "w");
    except:
        print "Could not open file " + outputFileName;
        return;

    for line in logFile:

        words = line.split(" ");
        thread = 0;
        time = 0;
        func = "";

        if(len(words) < 4):
           continue;

        try:
            func = words[1];
        except ValueError:
            print "Could not parse: " + line;
            continue;

        if(func == parent):
            if(words[0] == "-->"):
                childOn = True;
                numLinesChild = 0;
                parentLine = line;
            if(words[0] == "<--"):
                childOn = False;
                if(printedParentLine):
                    outputFile.write("%s" % line);
                    printedParentLine = False;

        if(func == child and childOn):
            if(not printedParentLine):
                outputFile.write("%s" % parentLine);
                printedParentLine = True;
            if(numLinesChild < numLinesChildThreshold):
                outputFile.write("%s" % line);
                numLinesChild = numLinesChild + 1;

    logFile.close();
    outputFile.close();

def main():

    parser = argparse.ArgumentParser(description=
                                     'Process performance log files');
    parser.add_argument('files', type=str, nargs='+',
                        help='log files to process');

    parser.add_argument('--parent', dest='parent');
    parser.add_argument('--child', dest='child');

    args = parser.parse_args();
    print args.files;
    print args.parent;
    print args.child;

    for fname in args.files:
        parse_file(fname, args.parent, args.child);


if __name__ == '__main__':
    main()
