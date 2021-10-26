#!/usr/bin/env python3

import argparse
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

    if (verbose):
        print(color.BLUE + color.BOLD +
              "Original " + fname + " data:" + color.END);
        print(df);

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

    print(color.RED + color.BOLD +
          "Normalizing by throughput in " + baselineDFName + color.END);

    baselineThroughput = dataFrames[baselineDFName]['throughput'].copy();

    for name, df in dataFrames.items():
        df['throughput'] = df['throughput']/baselineThroughput;

def example():

    df = pd.DataFrame()

    #the groups can vary 
    grp1 = 'MM-16GB'
    grp2 = 'MM-32GB'
    grp3 = 'NVCache-16GB'

    df['label'] = ['YCSB-A.read','YCSB-A.update','YCSB-C.read']
    df[grp1+'_int'] = [1, 1, 1]
    df[grp1+'_SD'] = [0.02, 0.01, 0.02]
    df[grp2+'_int'] = [1.05, 1.06, 1.26]
    df[grp2+'_SD'] = [0.02, 0.01, 0.02]
    df[grp3+'_int'] = [1.01, 1.21, 1.48]
    df[grp3+'_SD'] = [0, 0, 0.02]

    ax = df.plot.bar(x='label', 
                     y=[grp1+'_int',grp2+'_int',grp3+'_int'],
                     yerr=df[[grp1+'_SD',grp2+'_SD',grp3+'_SD']].T.values)
    print(df)
    ax = df.plot.bar(x='label', y=[grp1+'_int',grp2+'_int',grp3+'_int'], yerr=df[[grp1+'_SD', grp2+'_SD', grp3+'_SD']].values)
    plt.show();

def main():

    parser = argparse.ArgumentParser(description=
                                 'Show trace summary');

    parser.add_argument('files', type=str, nargs='*', help='input data files');
    parser.add_argument('-n', '--normalizeBy', dest='normalizeBy', type=str);
    args = parser.parse_args();

    if (len(args.files) == 0):
        parser.print_help();
        sys.exit(1);

    for fname in args.files:
        processFile(fname);

    for name, df in dataFrames.items():
        print(name);
        print("----------------");
        print(df);
        print("================\n");

    if (args.normalizeBy is not None):
        normalizeBy(args.normalizeBy);

    print(color.RED + color.BOLD +
          "Done " + color.END);

    for name, df in dataFrames.items():
        print(name);
        print("----------------");
        print(df);
        print("================\n");


if __name__ == '__main__':
    main()
