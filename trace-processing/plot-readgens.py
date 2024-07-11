#!/usr/bin/env python3

import argparse
import matplotlib.pyplot as plt
import os
import os.path
import re
import sys
import traceback
from argparse import RawTextHelpFormatter

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

def ERROR(msg):
    print(color.BOLD + color.RED + msg + color.END);
    sys.exit(1);
#
# The input files contain read generations, one per line for native eviction and
# simulated respectively.
#
def plot(nativeFname, simulatedFname):

    # Read the y-values
    with open(nativeFname, 'r') as nativeF:
        native = [int(line.strip()) for line in nativeF];
    with open(simulatedFname, 'r') as simulatedF:
        simulated = [int(line.strip()) for line in simulatedF];

    # Generate the x-values (sequential indices) for both datasets
    x_native = list(range(len(native)));
    x_simulated = list(range(len(simulated)));

    plt.figure(figsize=(10, 6))

    # Plot the numbers from the first file
    plt.scatter(x_native, native, c='blue', marker='o', label=nativeFname)

    # Plot the numbers from the second file
    plt.scatter(x_simulated, simulated, c='red', marker='x', label=simulatedFname)

    # Customize the plot
    plt.title("Read generations over time for native and simulated eviction in WiredTiger");
    plt.xlabel("Eviction event number");
    plt.ylabel("Read generation of evicted page")
    plt.grid(True);
    plt.legend();

    # Show the plot
    plt.savefig(simulatedFname.strip().split(".")[0] + ".png"); 
    plt.show();
    

def main():
    parser = argparse.ArgumentParser(description=
                                     "Plot read generations for native and simulated WiredTiger eviction algorithm",
                                     formatter_class=RawTextHelpFormatter);
    parser.add_argument('-n', '--native', dest='native', type=str, required=True);
    parser.add_argument('-s', '--simulated', dest='simulated', type=str, required=True);

    args = parser.parse_args();
    plot(args.native, args.simulated);

if __name__ == '__main__':
    main()
