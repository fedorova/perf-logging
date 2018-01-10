#!/usr/bin/env python

import argparse
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, HoverTool, FixedTicker
from bokeh.models import Legend, LegendItem
from bokeh.models import NumeralTickFormatter
from bokeh.models.annotations import Label
from bokeh.plotting import figure, output_file, show
import matplotlib
import numpy as np
import pandas as pd
import sys

# A static list of available CSS colors
colorList = [];

# Track if this color was already used in any legend.
colorAlreadyUsedInLegend = {};

lastColorUsed = 0;
funcToColor = {};
intervalBeginningsStack = [];


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

def add_legend(p, legendItems, numLegends):

    legend = Legend(items=legendItems, orientation = "horizontal");
    p.add_layout(legend, place='above');
    legendItems[:] = [];  # Empty the list.

    return (numLegends + 1);

def bokeh_plot(figure_title, legend, dataframe, y_max):

    global colorAlreadyUsedInLegend;

    MAX_ITEMS_PER_LEGEND = 5;
    numLegends = 0;
    legendItems = [];
    pixelsPerStackLevel = 30;
    pixelsPerLegend = 60;
    pixelsForTitle = 30;

    cds = ColumnDataSource(dataframe);

    hover = HoverTool(tooltips=[
        ("function", "@function"),
        ("duration", "@durations")
    ]);

    TOOLS = [hover];

    p = figure(title=figure_title, plot_width=1200,
               y_range = (0, max(y_max, y_max+1)),
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
           source=cds, line_color="lightgrey");

    xMax = dataframe['end'].max();
    yMax = dataframe['stackdepthNext'].max();

    averageDuration = dataframe['durations'].mean();
    maxDuration = dataframe['durations'].max();

    text = "Average duration: " + '{0:,.0f}'.format(averageDuration) + \
           ". Maximum duration: " + '{0:,.0f}'.format(maxDuration) + ".";
    mytext = Label(x=0, y=yMax, text=text,
                   text_color = "grey", text_font = "helvetica",
                   text_font_size = "10pt",
                   text_font_style = "italic");
    p.add_layout(mytext);

    #p.quad(left = dataframe.head(num)['start'],
    #       right = dataframe.head(num)['end'],
    #       bottom = dataframe.head(num)['stackdepth'],
    #       top = dataframe.head(num)['stackdepth'] + 1,
    #       color=dataframe.head(num)['color'],
    #       line_color="lightgrey");

    for func, fColor in funcToColor.iteritems():

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
            numLegends = add_legend(p, legendItems, numLegends);

    # Add whatever legend items did not get added
    if (len(legendItems) > 0):
        numLegends = add_legend(p, legendItems, numLegends);

    # Plot height is the function of the maximum call stack and the number of
    # legends
    p.plot_height =  (numLegends * pixelsPerLegend) \
                     + max((y_max+1) * pixelsPerStackLevel, 100) \
                     + pixelsForTitle;

    return p;


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

    colors = [];
    beginIntervals = [];
    dataFrame = None;
    durations = [];
    endIntervals = [];
    firstTimeStamp = sys.maxsize;
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
            intervalBegin, intervalEnd, function, stackDepth \
                = getIntervalData(row);

            if (intervalBegin < firstTimeStamp):
                firstTimeStamp =  intervalBegin;

            beginIntervals.append(intervalBegin);
            endIntervals.append(intervalEnd);
            durations.append(intervalEnd-intervalBegin);
            functionNames.append(function);
            stackDepths.append(stackDepth);
            stackDepthsNext.append(stackDepth + 1);
            colors.append(getColorForFunction(function));

            if (stackDepth > largestStackDepth):
                largestStackDepth = stackDepth;
        else:
            print("Invalid event in this line:");
            print(str(row[0]) + " " + str(row[1]) + " " + str(row[2]));
            continue;

    if (dataFrame is None):
        dict = {};
        dict['start'] = beginIntervals;
        dict['end'] = endIntervals;
        dict['function'] = functionNames;
        dict['durations'] = durations;
        dict['stackdepth'] = stackDepths;
        dict['stackdepthNext'] = stackDepthsNext;
        dict['color'] = colors;

        dataframe = pd.DataFrame(data=dict);

        dataframe['start'] = dataframe['start'] - firstTimeStamp;
        dataframe['end'] = dataframe['end'] - firstTimeStamp;

    return dataframe, largestStackDepth;

def processFileAndCreatePlot(fname):

    data = pd.read_csv(fname,
                       header=None, delimiter=" ",
                       index_col=2,
                       names=["Event", "Function", "Timestamp"],
                       dtype={"Event": np.int32, "Timestamp": np.int64},
                       thousands=",");

    intervalDataFrame, largestStackDepth = \
                                        createCallstackSeries(data.head(100));
    figure = bokeh_plot(fname, "functions", intervalDataFrame,
                        largestStackDepth + 1);
    return figure;


def main():

    figuresForAllFiles = [];

    for x in range(1000000):
        print '{0}\r'.format(x),
    print

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

    # output to static HTML file
    output_file(filename = "WT-log.html", title="Operation log");

    for fname in args.files:
        figure = processFileAndCreatePlot(fname);
        figuresForAllFiles.append(figure);

    show(column(figuresForAllFiles));

if __name__ == '__main__':
    main()
