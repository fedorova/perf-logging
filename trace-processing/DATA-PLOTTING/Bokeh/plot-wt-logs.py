#!/usr/bin/env python

from bokeh.models import ColumnDataSource, HoverTool, Legend, LegendItem
from bokeh.models import NumeralTickFormatter
from bokeh.plotting import figure, output_file, show
import matplotlib
import numpy as np
import pandas as pd


colorList = [];
lastColorUsed = 0;
largestStackDepth = 0;
funcToColor = {};
intervalBeginningsStack = [];


def initColorList():

    global colorList;

    colorList = matplotlib.colors.cnames.keys();

    for color in colorList:
        # Some browsers break if you try to give them 'sage'
        if (color == "sage"):
            colorList.remove(color);
        print(color);

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

def bokeh_plot_old(figure_title, file_to_save, legend, x_data,
              x_name, y_data, y_name):


    # output to static HTML file
    output_file(file_to_save);

    # create a new plot with a title and axis labels
    p = figure(title=figure_title, x_axis_label=x_name, y_axis_label=y_name,
               plot_width=800, plot_height=400);

    # add a line renderer with legend and line thickness
    p.line(x_data, y_data, legend=legend, line_width=2);

    # show the results
    show(p)


def bokeh_plot(figure_title, file_to_save, legend, dataframe, y_max):

    MAX_ITEMS_PER_LEGEND = 5;
    num = 100;
    numLegends = 0;
    legendItems = [];
    pixelsPerVisualRow = 60;

    # output to static HTML file
    output_file(file_to_save);

    cds = ColumnDataSource(dataframe.head(num));

    hover = HoverTool(tooltips=[
        ("function", "@function"),
        ("duration", "@start")
    ]);

    TOOLS = [hover];

    p = figure(title=figure_title, plot_width=1200,
               y_range = (0, max(y_max, y_max+1)),
               x_axis_label = "Time (CPU cycles)",
               y_axis_label = "Stack depth",
               tools = TOOLS
    );

    # No minor ticks or labels on the y-axis
    p.yaxis.minor_tick_line_color = None;
    p.yaxis.major_label_text_font_size = '0pt';

    p.xaxis.formatter = NumeralTickFormatter(format="0,")

    p.quad(left = 'start', right = 'end', bottom = 'stackdepth',
           top = 'stackdepthNext', color = 'color',
           source=cds, line_color="lightgrey");

    #p.quad(left = dataframe.head(num)['start'],
    #       right = dataframe.head(num)['end'],
    #       bottom = dataframe.head(num)['stackdepth'],
    #       top = dataframe.head(num)['stackdepth'] + 1,
    #       color=dataframe.head(num)['color'],
    #       line_color="lightgrey");

    for func, fColor in funcToColor.iteritems():
        r = p.quad(left=0, right=1, bottom=0, top=1, color=fColor);

        lItem = LegendItem(label = func,
                           renderers = [r]);
        legendItems.append(lItem);

        # Cap the number of items in a legend, so it can
        # fit horizontally.
        if (len(legendItems) == MAX_ITEMS_PER_LEGEND):
            legend = Legend(items=legendItems, orientation = "horizontal");
            p.add_layout(legend, place='above');
            numLegends += 1;
            legendItems[:] = []

    # Plot height is the function of the maximum call stack and the number of
    # legends
    p.plot_height = max((y_max + numLegends) * pixelsPerVisualRow, 200);

    show(p);


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

def createTimedeltaSeries(data):

    global largestStackDepth;

    colors = [];
    beginIntervals = [];
    dataFrame = None;
    endIntervals = [];
    functionNames = [];
    stackDepths = [];
    stackDepthsNext = [];

    for row in data.itertuples():
        # row[0] is the timestamp, row[1] is the event type,
        # row[2] is the function name.
        #
        if (row[1] == 0):
            markIntervalBeginning(row);
        elif (row[1] == 1):
            intervalBegin, intervalEnd, function, stackDepth \
                = getIntervalData(row);

            beginIntervals.append(intervalBegin);
            endIntervals.append(intervalEnd);
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
        dict['stackdepth'] = stackDepths;
        dict['stackdepthNext'] = stackDepthsNext;
        dict['color'] = colors;

        firstTimeStamp = beginIntervals[0];
        #print("First timestamp is " + str(firstTimeStamp));

        dataframe = pd.DataFrame(data=dict);

        dataframe['start'] = dataframe['start'] - firstTimeStamp;
        dataframe['end'] = dataframe['end'] - firstTimeStamp;

        #print dataframe;

    return dataframe;


def main():

    global largestStackDepth;
    global legendItems;

    initColorList();

    fname = 'optrack.0000060755.0000000021.txt';

    data = pd.read_csv(fname,
                       header=None, delimiter=" ",
                       index_col=2,
                       names=["Event", "Function", "Timestamp"],
                       dtype={"Event": np.int32, "Timestamp": np.int64},
                       thousands=",");

    intervalDataFrame = createTimedeltaSeries(data);
    bokeh_plot(fname, "WT-log.html", "functions", intervalDataFrame,
               largestStackDepth);

    #print  intervalDataFrame.index[0];

    #interval = pd.DataFrame({'start' : intervalDataFrame.index[0] });
    #interval['end'] = interval['start'] + intervalDataFrame;
    #cds = ColumnDataSource(interval);


    # Convert to time series. This allows you to index the data.
    # x_data = time = data.index.values;
    # y_data = series = data["Event"].values;

    #print(time);
    #print(series);

    #print(data);

    #print("=====================");
    #print(data.values.tolist());

    #x_data = series.to_xarray();
    #print(x_data);

    #x_data = list(data.keys());
    #y_data = list(data.values());

    #print(x_data);
    #print(y_data);

    #bokeh_plot("Function entry/exit events",
    #           "WT-log.html", "entry = 0, exit=1",
    #           x_data, "Time", y_data, "Enter/Exit");

if __name__ == '__main__':
    main()
