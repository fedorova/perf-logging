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

# A function name mapped to its corresponding color.
#
funcToColor = {};
lastColorUsed = 0;

# The smallest and the largest timestamps seen across all files.
#
firstTimeStamp = sys.maxsize;
lastTimeStamp = 0;

# Push operation opening records onto this callstack until the
# corresponding closing records are found.
#
intervalBeginningsStack = [];

# A dictionary that holds a reference to the raw dataframe for each file.
#
perFileDataFrame = {};

# A dictionary that holds the intervals data per function.
#
perFuncDF = {};

plotWidth = 1200;
pixelsForTitle = 30;
pixelsPerHeightUnit = 30;
pixelsPerWidthUnit = 5;

# The coefficient by which we multiply the standard deviation when
# setting the outlier threshold, in case it is not specified by the user.
#
STDEV_MULT = 1;


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

def plotOutlierHistogram(dataframe, maxOutliers, func, durationThreshold):

    global pixelsForTitle;
    global pixelsPerHeightUnit;
    global plotWidth;

    cds = ColumnDataSource(dataframe);

    figureTitle = "Occurrences of " + func + " that took longer than " \
                  + "{:,.0f}".format(durationThreshold) + " time units.";

    hover = HoverTool(tooltips = [
        ("interval start", "@lowerbound"),
        ("interval end", "@upperbound")]);

    TOOLS = [hover];

    p = figure(title = figureTitle, plot_width = plotWidth,
               plot_height = (maxOutliers + 1) * pixelsPerHeightUnit + \
               pixelsForTitle,
               y_range = (0, maxOutliers + 1),
               x_axis_label = "Execution timeline (CPU cycles)",
               y_axis_label = "Number of outliers", tools = TOOLS);

    p.yaxis.ticker = FixedTicker(ticks = range(0, maxOutliers+1));
    p.ygrid.ticker = FixedTicker(ticks = range(0, maxOutliers+1));
    p.xaxis.formatter = NumeralTickFormatter(format="0,");

    p.quad(left = 'lowerbound', right = 'upperbound', bottom = 'bottom',
           top = 'height', color = funcToColor[func], source = cds,
           line_color="lightgrey");

    return p;

def createCallstackSeries(data):

    global firstTimeStamp;
    global lastTimeStamp;

    beginIntervals = [];
    dataFrame = None;
    endIntervals = [];
    functionNames = [];
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
            functionNames.append(function);

        else:
            print("Invalid event in this line:");
            print(str(row[0]) + " " + str(row[1]) + " " + str(row[2]));
            continue;


    dict = {};
    dict['start'] = beginIntervals;
    dict['end'] = endIntervals;
    dict['function'] = functionNames;

    dataframe = pd.DataFrame(data=dict);
    dataframe['durations'] = dataframe['end'] - dataframe['start'];

    return dataframe;

def processFile(fname):

    global perFuncDF;

    rawData = pd.read_csv(fname,
                       header=None, delimiter=" ",
                       index_col=2,
                       names=["Event", "Function", "Timestamp"],
                       dtype={"Event": np.int32, "Timestamp": np.int64},
                       thousands=",");

    iDF = createCallstackSeries(rawData);

    perFileDataFrame[fname] = iDF;

    for func in funcToColor.keys():

        funcDF = iDF.loc[lambda iDF: iDF.function == func, :];
        #funcDF = funcDF.set_index('start');
        funcDF = funcDF.drop(columns = ['function']);

        if (not perFuncDF.has_key(func)):
            perFuncDF[func] = funcDF;
        else:
            perFuncDF[func] = pd.concat([perFuncDF[func], funcDF]);


#
# For each function, split the timeline into buckets. In each bucket
# show how many times this function took an unusually long time to
# execute.
#
# The parameter durationThreshold tells us when a function should be
# considered as unusually long. If this parameter is "-1" we count
# all functions whose duration exceeded the average by more than
# two standard deviations.
#
def createOutlierHistogramForFunction(func, funcDF, durationThreshold):

    global firstTimeStamp;
    global lastTimeStamp;
    global plotWidth;
    global pixelsPerWidthUnit;
    global STDEV_MULT;

    #
    # funcDF is a list of functions along with their start and end
    # interval and durations. We need to create a new dataframe where
    # we separate the entire timeline into a fixed number of periods
    # and for each period compute how many outlier durations were
    # observed. Then we create a histogram from this data.

    # Subtract the smallest timestamp from all the interval data.
    funcDF['start'] = funcDF['start'] - firstTimeStamp;
    funcDF['end'] = funcDF['end'] - firstTimeStamp;

    funcDF = funcDF.sort_values(by=['start'])

    # If duration threshold equals -1 compute the average and standard
    # deviation. Our actual threashold will be the value exceeding two
    # standard deviations from the average.
    #
    if (durationThreshold == -1):
        average = funcDF['durations'].mean();
        stdDev = funcDF['durations'].std();
        durationThreshold = average + STDEV_MULT * stdDev;

#        print(color.PURPLE + color.UNDERLINE + func + color.END);
#        print("Average duration: " + color.BOLD + str(average) + color.END);
#        print("Standard deviation: " + color.BOLD + str(stdDev) + color.END);
#        print;

    numColumns = plotWidth / pixelsPerWidthUnit;
    timeUnitsPerColumn = (lastTimeStamp - firstTimeStamp) / numColumns;

    lowerBounds = [];
    upperBounds = [];
    bucketHeights = [];
    maxOutliers = 0;

    for i in range(numColumns):
        lowerBound = i * timeUnitsPerColumn;
        upperBound = (i+1) * timeUnitsPerColumn;

        intervalDF = funcDF.loc[(funcDF['start'] >= lowerBound)
                                & (funcDF['end'] < upperBound)
                                & (funcDF['durations'] >= durationThreshold)];

        numOutliers = intervalDF.size;
        if (numOutliers > maxOutliers):
            maxOutliers = numOutliers;

        lowerBounds.append(lowerBound);
        upperBounds.append(upperBound);
        bucketHeights.append(numOutliers);

    if (maxOutliers == 0):
        return None;

    dict = {};
    dict['lowerbound'] = lowerBounds;
    dict['upperbound'] = upperBounds;
    dict['height'] = bucketHeights;
    dict['bottom'] = [0] * len(lowerBounds);
    dataframe = pd.DataFrame(data=dict);

    return plotOutlierHistogram(dataframe, maxOutliers, func,
                                durationThreshold);

def main():

    global perFuncDF;

    figuresForAllFunctions = [];

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

    # Generate a histogram of outlier durations
    for func in sorted(perFuncDF.keys()):
        funcDF = perFuncDF[func];
        figure = createOutlierHistogramForFunction(func, funcDF, -1);
        if (figure is not None):
            figuresForAllFunctions.append(figure);

    output_file(filename = "WT-outliers.html", title="Outlier histograms");
    show(column(figuresForAllFunctions));

if __name__ == '__main__':
    main()
