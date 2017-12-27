#!/usr/bin/env python

import argparse
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, CustomJS, HoverTool, FixedTicker
from bokeh.models import Legend, LegendItem
from bokeh.models import NumeralTickFormatter, OpenURL, TapTool
from bokeh.plotting import figure, output_file, reset_output, save, show
from bokeh.resources import CDN
import matplotlib
import numpy as np
import os
import pandas as pd
import sys
import traceback

# A directory where we store cross-file plots for each bucket of the outlier
# histogram.
#
bucketDir = "BUCKET-FILES";

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

# Data frames and largest stack depth for each file.
perFileDataFrame = {};
perFileLargestStackDepth = {};

plotWidth = 1200;
pixelsForTitle = 30;
pixelsPerHeightUnit = 30;
pixelsPerWidthUnit = 5;

# The coefficient by which we multiply the standard deviation when
# setting the outlier threshold, in case it is not specified by the user.
#
STDEV_MULT = 2;


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

    matchFound = False;

    if (intervalEnd[1] != 1):
        print("createTimedeltaObject: only rows with event type 1 can be used");
        print(str(intervalEnd));
        return None;

    if (len(intervalBeginningsStack) < 1):
        print("Nothing on the intervalBeginningsStack. I cannot find the " +
              "beginning for this interval.");
        print(str(intervalEnd));
        return None;

    while (not matchFound):
        intervalBegin = intervalBeginningsStack.pop();
        if (intervalBegin is None):
            print(color.RED + color.BOLD +
                  "Could not find the matching operation begin record " +
                  " for the following operation end record: " + color.END
                  + str(intervalEnd));
            return None;
        if (intervalBegin[2] != intervalEnd[2]):
            print(color.RED + color.BOLD +
                  "Operation end record does not match the available " +
                  "operation begin record. Your log file may be incomplete. " +
                  "Skipping the begin record."
                  + color.END);
            print("Begin: " + str(intervalBegin));
            print("End: " + str(intervalEnd));
        else:
            matchFound = True;

    # This value determines how deep we are in the callstack
    stackDepth = len(intervalBeginningsStack);

    return intervalBegin[0], intervalEnd[0], intervalEnd[2], stackDepth;

def plotOutlierHistogram(dataframe, maxOutliers, func, durationThreshold):

    global pixelsForTitle;
    global pixelsPerHeightUnit;
    global plotWidth;

    cds = ColumnDataSource(dataframe);

    figureTitle = "Occurrences of " + func + " that took longer than " \
                  + "{:,.0f}".format(durationThreshold) + " CPU cycles.";

    hover = HoverTool(tooltips = [
        ("interval start", "@lowerbound{0,0}"),
        ("interval end", "@upperbound{0,0}")]);

    TOOLS = [hover, "tap, reset"];

    p = figure(title = figureTitle, plot_width = plotWidth,
               plot_height = max(5, (maxOutliers + 1)) * pixelsPerHeightUnit + \
               pixelsForTitle,
               y_range = (0, maxOutliers + 1),
               x_axis_label = "Execution timeline (CPU cycles)",
               y_axis_label = "Number of outliers", tools = TOOLS);

    p.yaxis.ticker = FixedTicker(ticks = range(0, maxOutliers+1));
    p.ygrid.ticker = FixedTicker(ticks = range(0, maxOutliers+1));
    p.xaxis.formatter = NumeralTickFormatter(format="0,");

    p.quad(left = 'lowerbound', right = 'upperbound', bottom = 'bottom',
           top = 'height', color = funcToColor[func], source = cds,
           nonselection_fill_color=funcToColor[func],
           nonselection_fill_alpha = 1.0,
           line_color = "lightgrey",
           selection_fill_color = funcToColor[func],
           selection_line_color="grey"
    );

    url = "@bucketfiles";
    taptool = p.select(type=TapTool);
    taptool.callback = OpenURL(url=url);

    return p;

# From all timestamps subtract the smallest observed timestamp, so that
# our execution timeline begins at zero.
#
def normalizeIntervalData():

    global firstTimeStamp;
    global perFileDataFrame;

    for file, df in perFileDataFrame.iteritems():
        df['origstart'] = df['start'];
        df['start'] = df['start'] - firstTimeStamp;
        df['end'] = df['end'] - firstTimeStamp;

def createCallstackSeries(data):

    global firstTimeStamp;
    global lastTimeStamp;

    colors = [];
    beginIntervals = [];
    dataFrame = None;
    endIntervals = [];
    functionNames = [];
    largestStackDepth = 0;
    stackDepths = [];
    stackDepthsNext = [];
    thisIsFirstRow = True;

    for row in data.itertuples():
        # row[0] is the timestamp, row[1] is the event type,
        # row[2] is the function name.
        #
        if (row[1] == 0):
            markIntervalBeginning(row);
        elif (row[1] == 1):
            try:
                intervalBegin, intervalEnd, function, stackDepth \
                    = getIntervalData(row);
            except:
                print(color.RED + color.BOLD + " ...skipping." + color.END);
                continue;

            if (intervalBegin < firstTimeStamp):
                firstTimeStamp =  intervalBegin;
            if (intervalEnd > lastTimeStamp):
                lastTimeStamp = intervalEnd;

            colors.append(getColorForFunction(function));
            beginIntervals.append(intervalBegin);
            endIntervals.append(intervalEnd);
            functionNames.append(function);
            stackDepths.append(stackDepth);
            stackDepthsNext.append(stackDepth + 1);

        else:
            print("Invalid event in this line:");
            print(str(row[0]) + " " + str(row[1]) + " " + str(row[2]));
            continue;


    dict = {};
    dict['color'] = colors;
    dict['start'] = beginIntervals;
    dict['end'] = endIntervals;
    dict['function'] = functionNames;
    dict['stackdepth'] = stackDepths;
    dict['stackdepthNext'] = stackDepthsNext;

    dataframe = pd.DataFrame(data=dict);
    dataframe['durations'] = dataframe['end'] - dataframe['start'];

    return dataframe;

def addLegend(p, legendItems, numLegends):

    legend = Legend(items=legendItems, orientation = "horizontal");
    p.add_layout(legend, place='above');
    legendItems[:] = [];  # Empty the list.

    return (numLegends + 1);

# For each function we only show the legend once. In this dictionary we
# keep track of colors already used.
#
colorAlreadyUsedInLegend = {};

def generateBucketChartForFile(figureName, dataframe, y_max, x_min, x_max):

    global colorAlreadyUsedInLegend;
    global funcToColor;

    MAX_ITEMS_PER_LEGEND = 5;
    numLegends = 0;
    legendItems = [];
    pixelsPerStackLevel = 30;
    pixelsPerLegend = 60;
    pixelsForTitle = 30;

    cds = ColumnDataSource(dataframe);

    hover = HoverTool(tooltips=[
        ("function", "@function"),
        ("duration", "@durations{0,0}"),
        ("log file begin timestamp", "@origstart{0,0}")
    ]);

    TOOLS = [hover];

    p = figure(title=figureName, plot_width=1200,
               x_range = (x_min, x_max),
               y_range = (0, y_max+1),
               x_axis_label = "Time (CPU cycles)",
               y_axis_label = "Stack depth",
               tools = TOOLS
    );

    # No minor ticks or labels on the y-axis
    p.yaxis.major_tick_line_color = None;
    p.yaxis.minor_tick_line_color = None;
    p.yaxis.major_label_text_font_size = '0pt';
    p.yaxis.ticker = FixedTicker(ticks = range(0, y_max+1));
    p.ygrid.ticker = FixedTicker(ticks = range(0, y_max+1));

    p.xaxis.formatter = NumeralTickFormatter(format="0,")

    p.quad(left = 'start', right = 'end', bottom = 'stackdepth',
           top = 'stackdepthNext', color = 'color',
           source=cds);

    for func, fColor in funcToColor.iteritems():

        # If this function is not present in this dataframe,
        # we don't care about it.
        #
        boolVec = (dataframe['function'] == func);
        fDF = dataframe[boolVec];
        if (fDF.size == 0):
            continue;

        # If we already added a color to any legend, we don't
        # add it again to avoid redundancy in the charts and
        # in order not to waste space.
        #
        if (colorAlreadyUsedInLegend.has_key(fColor)):
            continue;
        else:
            colorAlreadyUsedInLegend[fColor] = True;

        r = p.quad(left=0, right=1, bottom=0, top=1, color=fColor);

        lItem = LegendItem(label = func,
                           renderers = [r]);
        legendItems.append(lItem);

        # Cap the number of items in a legend, so it can
        # fit horizontally.
        if (len(legendItems) == MAX_ITEMS_PER_LEGEND):
            numLegends = addLegend(p, legendItems, numLegends);

    # Add whatever legend items did not get added
    if (len(legendItems) > 0):
        numLegends = addLegend(p, legendItems, numLegends);

    # Plot height is the function of the maximum call stack and the number of
    # legends
    p.plot_height =  (numLegends * pixelsPerLegend) \
                     + max((y_max+1) * pixelsPerStackLevel, 100) \
                     + pixelsForTitle;

    return p;


def generateEmptyDataset():

    dict = {};
    dict['color'] = [0];
    dict['durations'] = [0];
    dict['start'] = [0];
    dict['end'] = [0];
    dict['function'] = [""];
    dict['stackdepth'] = [0];
    dict['stackdepthNext'] = [0];

    return pd.DataFrame(data=dict);

#
# If we have incomplete data, where some functions have a begin record,
# but not an end record, we may have an appearance of skipped stack levels.
#
# For instance:
#
# begin foo
# begin foo1
# begin foo2
# end   foo2
# end   foo
#
# foo will have stack level 0. foo1 will be skipped, foo2 will have
# stack level 2. That's because at the time we are assigning a stack level
# to foo2, we don't yet know that foo1 will have to be skipped -- what if
# we find a matching record later?
#
# Therefore, we go through the data and adjust all stack levels that appear
# skipped.
#
# The rule is that every function foo2 should be at the same level as the last
# function foo1 that completed prior to it.
#
def cleanUpIntervalRecords(bucketDF):

    df = bucketDF.sort_values(by=['start']);
    df = df.reset_index(drop = True);

    i = 0;
    prevStackLevel = df.at[i, 'stackdepth'];
    prevEndTimestamp = 0;

    for i in range(len(df.index)):

        if (prevEndTimestamp < df.at[i, 'start']):
            if ((df.at[i, 'stackdepth'] - prevStackLevel) > 0):
                df.at[i, 'stackdepth'] = prevStackLevel;
                df.at[i, 'stackdepthNext'] = df.at[i, 'stackdepth'] + 1;
        else:
            if ((df.at[i, 'stackdepth'] - prevStackLevel) > 1):
                df.at[i, 'stackdepth'] = prevStackLevel + 1;
                df.at[i, 'stackdepthNext'] = df.at[i, 'stackdepth'] + 1;

        prevStackLevel = df.at[i, 'stackdepth'];
        prevEndTimestamp = df.at[i, 'end'];

    return df;


#
# Here we generate plots that span all the input files. Each plot shows
# the timelines for all files, stacked vertically. The timeline shows
# the function callstacks over time from this file.
#
# Since a single timeline is too large to fit on a single screen, we generate
# a separate HTML file with plots for bucket "i". A bucket is a vertical slice
# across the timelines for all files. We call it a bucket, because it
# corresponds to a bucket in the outlier histogram.
#
def generateCrossFilePlotsForBucket(i, lowerBound, upperBound):

    global bucketDir;
    global colorAlreadyUsedInLegend;

    figuresForAllFiles = [];
    fileName = bucketDir + "/bucket-" + str(i) + ".html";

    reset_output();

    # The following dictionary keeps track of legends. We need
    # a legend for each new HTML file. So we reset the dictionary
    # before generating a new file.
    #
    colorAlreadyUsedInLegend = {};

    intervalTitle = "Interval " + "{:,}".format(lowerBound) + \
                    " to " + "{:,}".format(upperBound) + \
                    " CPU cycles";

    #print("Bucket " + str(i));
    #print("Generating bucket for interval " + intervalTitle);

    # Select from the dataframe for this file the records whose 'start'
    # and 'end' timestamps fall within the lower and upper bound.
    #
    for fname, fileDF in perFileDataFrame.iteritems():

        #print("\tfor file " + fname);

        bucketDF = fileDF.loc[(fileDF['start'] >= lowerBound)
                              & (fileDF['start'] < upperBound)];

        if (lowerBound == 11479487124):
            print("-----------------------------------");
            print("Before cleanup:");
            for row in bucketDF.iterrows():
                print row;

        #print("\tdataframe size: " + str(bucketDF.size));
        if (bucketDF.size == 0):
            #bucketDF = generateEmptyDataset();
            continue;

        bucketDF = cleanUpIntervalRecords(bucketDF);
        largestStackDepth = bucketDF['stackdepthNext'].max();
        figureTitle = fname + ": " + intervalTitle;
        figure = generateBucketChartForFile(figureTitle, bucketDF,
                                            largestStackDepth,
                                            lowerBound, upperBound);

        if (lowerBound == 11479487124):
            print("-----------------------------------");
            print("After cleanup:");
            for row in bucketDF.iterrows():
                print row;

        figuresForAllFiles.append(figure);

    if (len(figuresForAllFiles) > 0):
        savedFileName = save(column(figuresForAllFiles),
                             filename = fileName, title=intervalTitle,
                             resources=CDN);
    else:
        savedFileName = "no-data.html";

    return savedFileName;

# Generate plots of time series slices across all files for each bucket
# in the outlier histogram. Save each cross-file slice to an HTML file.
#
def generateTSSlicesForBuckets():

    global firstTimeStamp;
    global lastTimeStamp;
    global plotWidth;
    global pixelsPerWidthUnit;

    bucketFilenames = [];

    numBuckets = plotWidth / pixelsPerWidthUnit;
    timeUnitsPerBucket = (lastTimeStamp - firstTimeStamp) / numBuckets;

    for i in range(numBuckets):
        lowerBound = i * timeUnitsPerBucket;
        upperBound = (i+1) * timeUnitsPerBucket;

        fileName = generateCrossFilePlotsForBucket(i, lowerBound,
                                                       upperBound);

        percentComplete = float(i) / float(numBuckets) * 100;
        print(color.BLUE + color.BOLD + " Generating timeline charts... "),
        sys.stdout.write("%d%% complete  \r" % (percentComplete) );
        sys.stdout.flush();
        bucketFilenames.append(fileName);

    print(color.END);
    return bucketFilenames;

def processFile(fname):

    global perFileDataFrame;
    global perFuncDF;

    rawData = pd.read_csv(fname,
                       header=None, delimiter=" ",
                       index_col=2,
                       names=["Event", "Function", "Timestamp"],
                       dtype={"Event": np.int32, "Timestamp": np.int64},
                       thousands=",");

    print(color.BOLD + "file " + str(fname) + color.END);
    iDF = createCallstackSeries(rawData);

    perFileDataFrame[fname] = iDF;

    for func in funcToColor.keys():

        funcDF = iDF.loc[lambda iDF: iDF.function == func, :];
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
def createOutlierHistogramForFunction(func, funcDF, durationThreshold,
                                      bucketFilenames):

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

    funcDF = funcDF.sort_values(by=['start']);

    # If duration threshold equals -1 compute the average and standard
    # deviation. Our actual threashold will be the value exceeding two
    # standard deviations from the average.
    #
    if (durationThreshold == -1):
        average = funcDF['durations'].mean();
        stdDev = funcDF['durations'].std();
        durationThreshold = average + STDEV_MULT * stdDev;

    numBuckets = plotWidth / pixelsPerWidthUnit;
    timeUnitsPerBucket = (lastTimeStamp - firstTimeStamp) / numBuckets;

    lowerBounds = [];
    upperBounds = [];
    bucketHeights = [];
    maxOutliers = 0;

    for i in range(numBuckets):
        lowerBound = i * timeUnitsPerBucket;
        upperBound = (i+1) * timeUnitsPerBucket;

        bucketDF = funcDF.loc[(funcDF['start'] >= lowerBound)
                                & (funcDF['start'] < upperBound)
                                & (funcDF['durations'] >= durationThreshold)];

        numOutliers = bucketDF.size;
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
    dict['bucketfiles'] = bucketFilenames;

    dataframe = pd.DataFrame(data=dict);

    return plotOutlierHistogram(dataframe, maxOutliers, func,
                                durationThreshold);

def main():

    global bucketDir;
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

    # Normalize all intervals by subtracting the first timestamp.
    normalizeIntervalData();

    # Create a directory for the files that display the data summarized
    # in each bucket of the outlier histogram. We call these "bucket files".
    #
    if not os.path.exists(bucketDir):
        os.makedirs(bucketDir)

    # Generate plots of time series slices across all files for each bucket
    # in the outlier histogram. Save each cross-file slice to an HTML file.
    #
    fileNameList = generateTSSlicesForBuckets();

    totalFuncs = len(perFuncDF.keys());
    i = 0;
    # Generate a histogram of outlier durations
    for func in sorted(perFuncDF.keys()):
        funcDF = perFuncDF[func];
        figure = createOutlierHistogramForFunction(func, funcDF, -1,
                                                   fileNameList);
        if (figure is not None):
            figuresForAllFunctions.append(figure);

        i += 1;
        percentComplete = float(i) / float(totalFuncs) * 100;
        print(color.BLUE + color.BOLD + " Generating outlier histograms... "),
        sys.stdout.write("%d%% complete  \r" % (percentComplete) );
        sys.stdout.flush();

    print(color.END);
    reset_output();
    output_file(filename = "WT-outliers.html", title="Outlier histograms");
    show(column(figuresForAllFunctions));

if __name__ == '__main__':
    main()



