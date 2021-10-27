#!/usr/bin/env python3

import argparse
from cycler import cycler
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import sys

dataFrames = {};
verbose = False;

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

def extractFromFilename(name):

    return name.split('-')[0];

def processFile(fname):

    global verbose;

    df = pd.read_csv(fname, sep=r'[ :.]', engine='python', header=None,
                     names=['workload', 'j1', 'j2', 'j3', 'j4', 'j5', 'j6',
                              'operation', 'j8', 'j9', 'throughput', 'j11'],
                     usecols=['workload', 'operation', 'throughput']
    );

    # This computes the mean throughput for each operation type
    # in the workload.
    #
    finalDF = df.groupby(['workload', 'operation']).mean();

    # This computes the standard deviation.
    #
    stdDF = df.groupby(['workload', 'operation']).std();

    # This adds a column with standard deviation expressed as the fraction
    # of the mean.
    #
    finalDF['stdRelative'] = stdDF['throughput']/finalDF['throughput'];
    print(color.PURPLE + color.BOLD +
          "Transformed " + fname + " data:" + color.END);
    if (verbose):
        print(finalDF);

    dataSetName = extractFromFilename(fname);
    dataFrames[dataSetName] = finalDF;

#
# Normalize the throughput column of each dataframe by the values
# in the first dataframe of the set.
#
def normalizeBy(baselineDFName):

    global dataFrames;

    baselineThroughput = dataFrames[baselineDFName]['throughput'].copy();

    for name, df in dataFrames.items():
        df['throughput'] = df['throughput']/baselineThroughput;

#
# Build charts using all color maps, cycling through their colors.
#
def buildChartsFromColormaps(df, yNames, errNames, chartName, colormaps, reverseColors):

    for cmapName in colormaps:
        n = len(yNames);
        colors = [plt.get_cmap(cmapName)(1. * i/n) for i in range(n)];
        if (reverseColors):
            colors.reverse();

        print(cmapName);
        plt.rc('axes', prop_cycle=cycler('color', colors));

        ax = df.plot.bar(x=chartName, y=yNames, yerr=df[errNames].T.values);
        #ax.set_prop_cycle(cycler('color', colors));
        ax.set_ylabel('Normalized throughput');

        # Place a legend above this subplot, expanding itself to
        # fully use the given bounding box.
        plt.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc='lower left',
               ncol=3, mode="expand", borderaxespad=0., frameon=False);
        # Place a legend to the right of this smaller subplot.
        # plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0.)
        plt.tight_layout();

        # If we are using only one colormap, omit the colormap name from
        # the figure title.
        #
        if (len(colormaps) == 1):
            plt.savefig(chartName + ".png");
        else:
            plt.savefig(chartName + "=" + str(cmapName) + ".png");

def generateChart(baseline, chartName):

    global dataFrames;

    df = pd.DataFrame();

    #
    # The baseline dataframe is a multi-index, with data grouped by
    # workload and operation. Workload and operation are part of the
    # index, but we want to generate x-axis labels from them.
    # So we convert the original dataframe into a flat one, where
    # workload and operations each get their proper column.
    #
    baseDF = dataFrames[baseline];
    flattenedDF = pd.DataFrame(baseDF.to_records());
    flattenedDF['workload'] = flattenedDF['workload'].str.upper();

    #
    # This is the new dataframe that will be plotted. We
    # begin by creating a column that contains a concatenation
    # of the workload name and the operation type.
    #
    df[chartName] = flattenedDF['workload'].map(str) + "." + \
                  flattenedDF['operation'].map(str);

    #
    # We gather the throughput and relative standard deviation from
    # all the data frames we want to display and append them to the
    # output dataframe.
    #
    yNames = [];
    errNames = [];
    for name, data in dataFrames.items():
        df[name] = data['throughput'].tolist();
        df[name+'_SDR'] = data['stdRelative'].tolist();
        yNames.append(name);
        errNames.append(name+'_SDR');

    print(df);

    #
    # Sequential colormaps I like:
    #
    # PiYG (reversed), PRGn (reversed), PuOr_r (reversed), PuRd_r (reversed),
    # RdBu (reversed), RdBu_r (reversed), Spectral (reversed)
    # BrBg, BuPu.
    #
    # buildChartsFromColormaps(df, yNames, errNames, chartName, plt.colormaps());
    #
    colormaps = ['PRGn'];
    buildChartsFromColormaps(df, yNames, errNames, chartName, colormaps, True);

def main():

    parser = argparse.ArgumentParser(description=
                                 'Show trace summary');

    parser.add_argument('files', type=str, nargs='*', help='input data files');
    parser.add_argument('-n', '--normalizeBy', dest='normalizeBy', type=str);
    parser.add_argument('-N', '--name', dest='name', type=str);
    args = parser.parse_args();

    if (len(args.files) == 0):
        parser.print_help();
        sys.exit(1);

    for fname in args.files:
        processFile(fname);

    print(color.BLUE + color.BOLD + "Original data:" + color.END);

    for name, df in dataFrames.items():
        print(name);
        print("----------------");
        print(df);
        print("================\n");

    if (args.normalizeBy is not None):
        print(color.RED + color.BOLD +
              "Normalizing by throughput in " + args.normalizeBy + color.END);
        normalizeBy(args.normalizeBy);
        print(color.RED + color.BOLD + "Done " + color.END);

    for name, df in dataFrames.items():
        print(name);
        print("----------------");
        print(df);
        print("================\n");

    generateChart(args.normalizeBy, args.name);

if __name__ == '__main__':
    main()
