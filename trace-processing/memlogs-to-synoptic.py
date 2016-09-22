#!/usr/bin/python -tt

import sys
import argparse

#
# Produced an abridged trace for synoptic, filtering out the functions that
# are not in the list of functions supplied in the second argument.
#
def parse_file(fname, funcs):

    # The function we are currently processing
    currentFuncStack = [];
    currentFunc = "";

    # We will produce a separate output file for each function that passes
    # the filter.
    #
    outputFiles = {};

    # When the filter level is zero, we are not writing any records to the file.
    # We increment the filter value every time we encounter an entry into the
    # desired function. We decrement the filter when we encounter an exit
    # statement. Increment/decrement is required to support nesting, i.e., if
    # the desired functions are nested.
    #
    filterLevel = 0;

    if(fname is not None):
        try:
            logFile = open(fname, "r");
            print "Parsing file " + fname;
        except:
            print "Could not open file " + fname + " for reading";
            return;

    outputFileName = fname + ".synoptic-memory";
    for func in funcs:
        outputFileName = fname + ".synoptic-memory." + func;
        try:
            outputFiles[func] = open(outputFileName, "w");
        except:
            print "Could not open file " + outputFileName + " for writing";
            return;

    for line in logFile:
        words = line.split(" ");

        if(len(words) < 1):
            continue;

        # This is the function entry record. See if this function passes
        # the filter. If so, turn on memory access logging.
        #
        if ((words[0] == "-->" or words[0] == "<--") and len(words) > 3):
            func = words[1];
            event_type = "";

            if (func in funcs and words[0] == "-->"):
                currentFunc = func;
                currentFuncStack.append(currentFunc);
                filterLevel = filterLevel + 1;
                print("entering " + func + ", filter level "
                      + str(filterLevel));

            if (filterLevel > 0):

                if (words[0] == "-->"):
                    event_type = "enter";
                elif (words[0] == "<--"):
                    event_type = "exit";

                outputFile = outputFiles[currentFunc];
                outputFile.write(event_type + " " + func + "\n");
                print("logging " + func + ", filter level " + str(filterLevel));

            if (func in funcs and words[0] == "<--"):
                currentFuncStack.pop();
                filterLevel = filterLevel - 1;
                if (len(currentFuncStack) > 0):
                    currentFunc = currentFuncStack[len(currentFuncStack) - 1];
                print("exiting " + func + ", filter level "
                            + str(filterLevel));


        # This is a memory access record. Log it if the filter is on.
        #
        elif (words[0] == "@" and filterLevel > 0 and len(words) > 4):

            if (words[4] == "R"):
                accessType = "read";
            else:
                accessType = "write";

            outputFile = outputFiles[currentFunc];
            outputFile.write(accessType + " " + words[2] + " " +
                             words[3] + "\n");


def main():

    parser = argparse.ArgumentParser(description=
                                     'Process performance log files');
    parser.add_argument('files', type=str, nargs='+',
                        help='log files to process');

    parser.add_argument('--func', '-f', dest='func', required='True', type=str,\
                        action='append', help='function names to include');
    args = parser.parse_args();

    print args.func

    for fname in args.files:
        parse_file(fname, args.func);

if __name__ == '__main__':
    main()
