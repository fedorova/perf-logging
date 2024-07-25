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

	plotName = None;
	x_native = None;
	x_simulated = None;

	# Read the y-values
	try:
		nativeF = open(nativeFname, 'r');
		native = [int(line.strip()) for line in nativeF];
		x_native = list(range(len(native)));
	except:
		print(f"No native trace provided. File name is {nativeFname}");

	try:
		simulatedF = open(simulatedFname, 'r');
		simulated = [int(line.strip()) for line in simulatedF];
		x_simulated = list(range(len(simulated)));
	except:
		print(f"No simulated trace provided. File name is {simulatedFname}");

	plt.figure(figsize=(10, 6))

	if (x_native is not None):
		print(f"{len(x_native)} native events.");
		plt.scatter(x_native, native, c='blue', marker='o', label=nativeFname)
	if (x_simulated is not None):
		print(f"{len(x_simulated)} simulated events.");
		plt.scatter(x_simulated, simulated, c='red', marker='x', label=simulatedFname)

	# Customize the plot
	plt.title("Read generations over time for eviction in WiredTiger");
	plt.xlabel("Eviction event number");
	plt.ylabel("Read generation of evicted page")
	plt.grid(True);
	plt.legend();

	# Show the plot
	if (simulatedFname is not None):
		plotName = simulatedFname.strip().split(".")[0] + "-simulated";
	if(nativeFname is not None):
		if (plotName is None):
			plotName = nativeFname.strip().split(".")[0];
		plotName = plotName + "-native";
	if (simulatedFname is None and nativeFname is None):
		print("No data provided");
		return;

	plt.savefig(plotName + ".png");
	plt.show();

def main():
    parser = argparse.ArgumentParser(description=
                                     "Plot read generations for native and simulated WiredTiger eviction algorithm",
                                     formatter_class=RawTextHelpFormatter);
    parser.add_argument('-n', '--native', dest='native', type=str);
    parser.add_argument('-s', '--simulated', dest='simulated', type=str);

    args = parser.parse_args();
    plot(args.native, args.simulated);

if __name__ == '__main__':
    main()
