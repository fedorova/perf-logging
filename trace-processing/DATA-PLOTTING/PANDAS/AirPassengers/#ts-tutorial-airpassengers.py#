#!/usr/bin/env python

import pandas as pd
import numpy as np
import matplotlib.pylab as plt
from matplotlib.pylab import rcParams
from statsmodels.tsa.stattools import adfuller


def test_stationarity(timeseries):

    # Determing rolling statistics
    rolmean = timeseries.rolling(window=12,center=False).mean();
    # rolstd = pd.rolling_std(timeseries, window=12)
    rolstd = timeseries.rolling(window=12,center=False).std();

    # Plot rolling statistics:
    orig = plt.plot(timeseries, color='blue',label='Original')
    mean = plt.plot(rolmean, color='red', label='Rolling Mean')
    std = plt.plot(rolstd, color='black', label = 'Rolling Std')
    plt.legend(loc='best')
    plt.title('Rolling Mean & Standard Deviation')
    plt.savefig('stationarity-test.png');

    # Perform Dickey-Fuller test:
    print 'Results of Dickey-Fuller Test:'
    dftest = adfuller(timeseries, autolag='AIC')
    dfoutput = pd.Series(dftest[0:4], index=['Test Statistic','p-value',
                                             '#Lags Used',
                                             'Number of Observations Used'])
    for key,value in dftest[4].items():
        dfoutput['Critical Value (%s)'%key] = value
    print dfoutput


def dateparse(dates):

    return pd.datetime.strptime(dates, '%Y-%m');


def main():

    rcParams['figure.figsize'] = 15, 6

    # Read the data
    data = pd.read_csv('AirPassengers.csv', parse_dates=['Month'],
                       index_col='Month',date_parser=dateparse)

    # Various ways to print the data
    print data.head()

    print '\n Data Types:'
    print data.dtypes;
    print data.index;

    # Convert to time series. This allows you to index the data.
    ts = data["#Passengers"];
    print ts;

    print ts['1960-12-01'];

    print ts['1949-01-01':'1949-05-01'];
    print ts['1949'];

    # Plot the data and save the figure to a file

    # This line is needed. Without it the figures generated below do
    # not show the data we want on the x-axis.
    #
    ts.plot();
    plt.plot(ts);
    plt.show();
    plt.savefig("fig.pdf");

    # Perform stationarity analysis and show the results
    test_stationarity(ts);

    ts1 = ts;
    ts2 = ts;
    ts3 = ts;

    ts1.plot();
    ts2.plot();
    ts3.plot();

    # Create many plots in one figure.

    plt.subplot(311);
    plt.plot(ts1, label="First one");

    plt.subplot(312);
    plt.plot(ts2, label="Second one");

    plt.subplot(313);
    plt.plot(ts3, label="Second one");
    plt.tight_layout();
    plt.show();

if __name__ == '__main__':
    main()
