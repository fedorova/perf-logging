#!/usr/bin/env python

import argparse
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, HoverTool, FixedTicker
from bokeh.models import Legend, LegendItem
from bokeh.models import NumeralTickFormatter
from bokeh.plotting import figure, output_file, show
import matplotlib
import numpy as np
import pandas as pd
import sys

# A static list of available CSS colors
colorList = [];

# A function name mapped to its corresponding color.
funcToColor = {};
lastColorUsed = 0;

# Push operation opening records onto this callstack until the
# corresponding closing records are found.
#
intervalBeginningsStack = [];

# A dictionary that holds a reference to the raw dataframe for each file.
perFileDataFrame = {};


def initColorList():

    global colorList;

    colorList = matplotlib.colors.cnames.keys();

    for color in colorList:
        # Some browsers break if you try to give them 'sage'
        if (color == "sage"):
            colorList.remove(color);

#
# Each unique function name gets a unique color.
# If we run out of colors, we repeat them from the
# beginning of the list.
#
def getColorForFunction(function):

    global colorList;
    global lastColorUsed;
    global funcToColor;

    if not funcToColor.has_key(function):
        funcToColor[function] = colorList[lastColorUsed % len(colorList)];
        lastColorUsed += 1;

    return funcToColor[function];


    intervalBeginningsStack.append(row);

def markIntervalBeginning(row):

    global intervalBeginningsStack;

    intervalBeginningsStack.append(row);

#
# An intervalEnd is a tuple of three items.
# item #0 is the timestamp,
# item #1 is the event type,
# item #2 is the function name.
#
def getIntervalData(intervalEnd):

    global intervalBeginningsStack;
    if (intervalEnd[1] != 1):
        print("createTimedeltaObject: only rows with event type 1 can be used");
        print(str(intervalEnd));
        return;

    if (len(intervalBeginningsStack) < 1):
        print("Nothing on the intervalBeginningsStack. I cannot find the " +
              "beginning for this interval.");
        print(str(intervalEnd));
        return;

    intervalBegin = intervalBeginningsStack.pop();
    if (intervalBegin[2] != intervalEnd[2]):
        print("Interval end does not match the available interval beginning.");
        print("Begin: " + str(intervalBegin));
        print("End: " + str(intervalEnd));
        return;

    # This value determines how deep we are in the callstack
    stackDepth = len(intervalBeginningsStack);

    return intervalBegin[0], intervalEnd[0], intervalEnd[2], stackDepth;

def createCallstackSeries(data):

#    colors = [];
    beginIntervals = [];
    dataFrame = None;
#    durations = [];
    endIntervals = [];
    firstTimeStamp = sys.maxsize;
    lastTimeStamp = 0;
    functionNames = [];
#    largestStackDepth = 0;
#    stackDepths = [];
#    stackDepthsNext = [];
    thisIsFirstRow = True;

    for row in data.itertuples():
        # row[0] is the timestamp, row[1] is the event type,
        # row[2] is the function name.
        #
        if (row[1] == 0):
            markIntervalBeginning(row);
        elif (row[1] == 1):
            intervalBegin, intervalEnd, function, stackDepth \
                = getIntervalData(row);

            if (intervalBegin < firstTimeStamp):
                firstTimeStamp =  intervalBegin;
            if (intervalEnd > lastTimeStamp):
                lastTimeStamp = intervalEnd;

            getColorForFunction(function);
            beginIntervals.append(intervalBegin);
            endIntervals.append(intervalEnd);
#            durations.append(intervalEnd-intervalBegin);
            functionNames.append(function);
#            stackDepths.append(stackDepth);
#            stackDepthsNext.append(stackDepth + 1);
#            colors.append(getColorForFunction(function));

#            if (stackDepth > largestStackDepth):
#                largestStackDepth = stackDepth;
        else:
            print("Invalid event in this line:");
            print(str(row[0]) + " " + str(row[1]) + " " + str(row[2]));
            continue;


    dict = {};
    dict['start'] = beginIntervals;
    dict['end'] = endIntervals;
    dict['function'] = functionNames;
#    dict['durations'] = durations;
#        dict['stackdepth'] = stackDepths;
#        dict['stackdepthNext'] = stackDepthsNext;
#        dict['color'] = colors;

    dataframe = pd.DataFrame(data=dict);

    dataframe['durations'] = dataframe['end'] - dataframe['start'];

#    dataframe['start'] = dataframe['start'] - firstTimeStamp;
#    dataframe['end'] = dataframe['end'] - firstTimeStamp;

    return dataframe, firstTimeStamp, lastTimeStamp;

def processFile(fname):

    rawData = pd.read_csv(fname,
                       header=None, delimiter=" ",
                       index_col=2,
                       names=["Event", "Function", "Timestamp"],
                       dtype={"Event": np.int32, "Timestamp": np.int64},
                       thousands=",");

    iDF, firstTimeStamp, lastTimeStamp = createCallstackSeries(rawData);

    perFileDataFrame[fname] = iDF;

    for func in funcToColor.keys():
        print(func);
        perFuncDF = iDF.loc[lambda iDF: iDF.function == func, :];
        print(perFuncDF);

def main():

    figuresForAllFiles = [];

    # Set up the argument parser
    #
    parser = argparse.ArgumentParser(description=
                                 'Visualize operation log');
    parser.add_argument('files', type=str, nargs='*',
                        help='log files to process');
    args = parser.parse_args();

    if (len(args.files) == 0):
        parser.print_help()
        sys.exit(1)

    # Get names of standard CSS colors that we will use for the legend
    initColorList();

    # Parallelize this later, so we are working on files in parallel.
    for fname in args.files:
        processFile(fname);

if __name__ == '__main__':
    main()
