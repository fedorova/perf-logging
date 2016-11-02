#!/usr/bin/python -tt

import sys
import argparse
import re
import operator
import colorsys

class HSL:
    def __init__(self, h, s, l):
	self.h = h;
	self.s = s;
	self.l = l;

    #
    # Code borrowed from http://www.rapidtables.com/convert/color/hsl-to-rgb.htm
    #
    def toRGB(self):
	h = float(self.h);
	s = self.s;
	l = self.l;

	if(h < 0 or h > 360):
	    return -1, -1, -1;
	if(s < 0 or s > 1):
	    return -1, -1, -1;
	if(l < 0 or l > 1):
	    return -1, -1, -1;

	C = (1 - abs(2*l - 1)) * s;
	X = C * (1 - abs(h / 60 % 2 -1));
	m = l - C/2;

	if(h >= 0 and h < 60):
	    r = C;
	    g = X;
	    b = 0;
	elif(h >= 60 and h < 120):
	    r = X;
	    g = C;
	    b = 0;
	elif(h >= 120 and h < 180):
	    r = 0;
	    g = C;
	    b = 0;
	elif(h >= 180 and h < 240):
	    r = 0;
	    g = X;
	    b = C;
	elif(h >= 240 and h < 300):
	    r = X;
	    g = 0;
	    b = C;
	elif(h >= 300 and h <= 360):
	    r = C;
	    g = 0;
	    b = X;

	r = int(round((r + m) * 255));
	g = int(round((g + m) * 255));
	b = int(round((b + m) * 255));

	return r, g, b;

    def toHex(self):
	r, g, b = self.toRGB();

	hexString = "#" + "%0.2X" % int(r) + "%0.2X" % int(g) + "%0.2X" % int(b)
	return hexString;

def isInt(s):
    try:
	int(s);
	return True;
    except ValueError:
	return False;

def buildColorList():

    colorRange = [];
    baseHue = 360;
    saturation = 0.70;
    lightness = 0.56;
    lightInc = 0.02;

    for i in range(0, 14):
	hslColor = HSL(baseHue - i * 20, saturation, lightness + lightInc * i,);
	hexColor = hslColor.toHex();
	colorRange.append(hexColor);

    return colorRange;

def buildFuncPerformanceDict(performanceSummaryFile):

    totalExecutionTime = 0;
    percentRuntime = {}; # Percent of total runtime keyed by function name

    for line in performanceSummaryFile:
	if (line.startswith("Total trace time:")):
	    words = line.split(" ");
	    try:
		totalExecutionTime = long(words[3]);
	    except:
		print("Could not parse total execution time in:");
		print(line);
		return;
	elif (line.startswith("***")):
	    # We expect to see the function name, followed by the number
	    # of times it was called, and followed by the total time we
	    # spent in this function.
	    words = re.split("\s|\t", line);
	    if(len(words) < 4):
		print("Expecting at least four words in this line:");
		print(line);
		print("Found " + str(len(words)));
		for i in range(0, len(words)):
		    print("word " + str(i) + " is " + words[i]);
		continue;

	    funcName = words[1];
	    try:
		totalTimeInFunc = long(words[3]);
	    except:
		continue;

	    percentInFunc = float(totalTimeInFunc) / float(totalExecutionTime) \
			    * 100;

	    if(not percentRuntime.has_key(funcName)):
		percentRuntime[funcName] = percentInFunc;
	    else:
		printf("Seeing function " + funcName + " more than once");

    sortedByPercentRuntime = sorted(percentRuntime.items(),
				    key=operator.itemgetter(1));

    return sortedByPercentRuntime;

#
# The first argument is the baseline synoptic dot file. The second
# argument is the sorted list of tuples, where the first item in each tuple is
# the function name, and the second item is the percent runtime spent in this
# function. The tuples are sorted in the ascending order.
#
def enhanceDotFile(outputFileName, synopticDotFile, perfTupleList):

    funcWithColorCode = {};
    rgbArray = buildColorList();
    lastPercent = 0.0;

    try:
	enhancedDotFile = open(outputFileName, "w");
    except:
	print("Could not open file " + outputFileName + " for writing.");
	return;

    #
    # Functions are sorted in perfTupleList ascending order according to percent
    # of time they contribute to the total execution time. Iterate over this
    # list in reverse order and pick a color to correspond to the function
    for tuple in reversed(perfTupleList):
	func = tuple[0];
	percent = tuple[1];
	percentStr = str(round(percent));

	# Let's find the color for this percent value.
	#
	idx = int(round((100.0 - percent) / 7.5));
	funcWithColorCode[func] = [rgbArray[idx], percentStr];

    #
    # Read the dot file and enhance it with the color codes assigned to the
    # functions.
    #
    for line in synopticDotFile:
	strLine = line.strip();
	words = strLine.split(" ");

	if (len(words) < 2):
	    enhancedDotFile.write(line);
	    continue;
	if (line.find('digraph') >= 0):
	    enhancedDotFile.write(line);
	    enhancedDotFile.write("graph [fontname = \"Helvetica\"];\n");
	    enhancedDotFile.write("node  [fontname = \"Helvetica\"];\n");
	    enhancedDotFile.write("edge  [fontname = \"Helvetica\"];\n");

	elif (isInt(words[0]) and line.find("label=") > 0):
	    #
	    # We expect to see something like this:
	    # 0 [label="enter __evict_clear_all_walks"];
	    #
	    nodeName = (line.split('label='))[1];
	    nodeName = nodeName.strip();
	    nodeName = nodeName.rstrip(';');
	    nodeName = nodeName.rstrip(']');
	    nodeName = nodeName.rstrip('"');
	    nodeName = nodeName.lstrip('"');

	    nodeNameWords = nodeName.split(" ");
	    if(len(nodeNameWords) < 2):
		enhancedDotFile.write(line);
		continue;
	    if(nodeNameWords[0] == "enter" or nodeNameWords[0] == "exit"):
		funcName = nodeNameWords[1];
		if(funcWithColorCode.has_key(funcName)):
		    colorCode = funcWithColorCode[funcName][0];
		    percent = funcWithColorCode[funcName][1];

		    outputString = "  " + words[0] + " [label=\"" + \
				   nodeNameWords[0] + " " + funcName + \
				   "\n" + percent + "%\"" + \
				   ",style=filled," + \
				   "fillcolor=\"" + colorCode + \
				   "\"];\n";
		    enhancedDotFile.write(outputString);
		else:
		    enhancedDotFile.write(line);
	    else:
		enhancedDotFile.write(line);
	else:
	    enhancedDotFile.write(line);

def parse_file(fname):

    synopticDotFileName = "";
    performanceSummaryFileName = "";
    synopticDotFile = None;
    performanceSummaryFile = None;

    synopticDotFileName = fname + ".synoptic.dot";
    performanceSummaryFileName = fname + ".summary";

    try:
	synopticDotFile = open(synopticDotFileName, "r");
    except:
	print "Could not open file " + synopticDotFileName;
	return;

    try:
	performanceSummaryFile = open(performanceSummaryFileName, "r");
    except:
	print "Could not open file " + performanceSummaryFileName;
	return;

    perfData = buildFuncPerformanceDict(performanceSummaryFile);
    enhanceDotFile(fname + ".synoptic-enhanced.dot", synopticDotFile, perfData);

def main():
    parser = argparse.ArgumentParser(description=
				     'Enhance synoptic charts with '
				     'performance characteristics');
    parser.add_argument('files', type=str, nargs='*',
			help='log files to process');
    args = parser.parse_args();

    if(len(args.files) > 0):
	for fname in args.files:
	    parse_file(fname);
#
# Arguments are two files: one is the summary file for the trace, the
# other one is the dot file for the synoptic chart. We parse the summary
# to figure out how much time the functions took to run relative to each
# other and augment the dot file to visually represent this information
# by using bright colours and large font sizes for time-consuming functions.
#

if __name__ == '__main__':
    main()
