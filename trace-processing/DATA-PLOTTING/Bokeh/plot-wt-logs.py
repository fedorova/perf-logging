#!/usr/bin/env python


from bokeh.plotting import figure, output_file, show
import matplotlib
import numpy as np
import pandas as pd


colorList = [];
intervalBeginningsStack = [];

def initColorList():

    global colorList;

    colorList = matplotlib.colors.cnames.keys();

    for color in colorList:
        print(color);


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

def bokeh_plot(figure_title, file_to_save, legend, dataframe):

     # output to static HTML file
    output_file(file_to_save);

    p = figure(title=figure_title, plot_width=800, plot_height=400,
               x_axis_label = "Time (CPU cycles)",
               y_axis_label = "Stack depth");

    p.quad(left = dataframe.head()['start'], right = dataframe.head()['end'],
           bottom = dataframe.head()['stackdepth'],
           top = dataframe.head()['stackdepth'] + 1,
           color=["firebrick", "navy", "deeppink", "deepskyblue", "dimgrey"]);

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

    beginIntervals = [];
    dataFrame = None;
    endIntervals = [];
    functionNames = [];
    stackDepths = [];

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

        firstTimeStamp = beginIntervals[0];
        print("First timestamp is " + str(firstTimeStamp));

        dataframe = pd.DataFrame(data=dict);

        dataframe['start'] = dataframe['start'] - firstTimeStamp;
        dataframe['end'] = dataframe['end'] - firstTimeStamp;

        print dataframe;

    return dataframe;


def main():

    initColorList();

    data = pd.read_csv('optrack.0000060755.0000000021.txt',
                       header=None, delimiter=" ",
                       index_col=2,
                       names=["Event", "Function", "Timestamp"],
                       dtype={"Event": np.int32, "Timestamp": np.int64},
                       thousands=",");

    intervalDataFrame = createTimedeltaSeries(data);
    bokeh_plot("Log file", "WT-log.html", "functions", intervalDataFrame);

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
