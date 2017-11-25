#!/usr/bin/env python

import pandas as pd
import numpy as np
from bokeh.plotting import figure, output_file, show


def bokeh_plot(figure_title, file_to_save, legend, x_data,
              x_name, y_data, y_name):


    # output to static HTML file
    output_file(file_to_save);

    # create a new plot with a title and axis labels
    p = figure(title=figure_title, x_axis_label=x_name, y_axis_label=y_name,
               x_axis_type='datetime', plot_width=800, plot_height=400);

    # add a line renderer with legend and line thickness
    p.line(x_data, y_data, legend=legend, line_width=2);

    # show the results
    show(p)


def dateparse(dates):

    return pd.datetime.strptime(dates, '%Y-%m');


def main():

    data = pd.read_csv('AirPassengers.csv', parse_dates=['Month'],
                       index_col='Month',date_parser=dateparse);

    # Convert to time series. This allows you to index the data.
    x_data = time = data.index.values;
    y_data = series = data["#Passengers"].values;

    print(time);
    print(series);

    #print(data);

    #print("=====================");
    #print(data.values.tolist());

    #x_data = series.to_xarray();
    #print(x_data);

    #x_data = list(data.keys());
    #y_data = list(data.values());

    #print(x_data);
    #print(y_data);

    bokeh_plot("Air Passengers", "air_passengers.html", "Number of passengers",
               x_data, "Time line", y_data, "Number of passengers");

if __name__ == '__main__':
    main()
