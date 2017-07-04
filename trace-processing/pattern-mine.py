#!/usr/bin/env python2.7

import argparse
import colorsys
import errno
import gzip
import json
import math
from multiprocessing import Process, Queue, Value
import multiprocessing
import networkx as nx
import operator
import os
import os.path
import platform
import re
import resource
import shutil
import subprocess
import sys
import time
import traceback

dbFile = None;
dbFileName = "trace.sql";
funcToId = {};
generateTextFiles = False;
graphFilePostfix = None;
graphType = None;
htmlDir = "./";
htmlTemplate = None;
multipleAcquireWithoutRelease = 0;
noMatchingAcquireOnRelease = 0;
outliersFile = None;
patterns = {};
percentThreshold = 0.0;
recID = 0;
separator = ";";
shortenFuncName = True;
summaryCSV = False;
summaryTxt = False;
treatLocksSpecially = False;
totalNodes = 0;
totalRecords = 0;
tryLockWarning = 0;
verbose = False;

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

#
# LogRecord contains all the fields we expect in the log record.

class LogRecord:
    def __init__(self, func, op, thread, time, otherInfo):
        self.func = func;
        self.op = op;
        self.thread = thread;
        self.time = long(time);
        self.otherInfo = otherInfo;
        self.filtered = False;

    def fullName(self):

        # otherInfo typically includes argument values. We append
        # it to the function name.
        #
        if (self.otherInfo is not None):
            return self.func + "::" + self.otherInfo;
        else:
            return self.func;

    # Each log record has an id. The constraint is that the entry
    # and exit to the same function invocation must have the same id.
    # Different invocations for identical functions would have different
    # ids.
    #
    def setID(self, id):
        self.id = id;

    def printLogRecord(self):
        print(self.op + " " + self.func + " " + str(self.thread) + " "
              + str(self.time));

    # This is for writing records into a file that contains the entire
    # trace in the format that is easily importable into a database.
    # We use delimiters that are default for MonetDB: "|".
    #
    def writeToDBFile(self, file, duration):

        file.write(str(self.id) + "|");

        if (self.op == "enter"):
            file.write("0");
        elif (self.op == "exit"):
            file.write("1");
        file.write("|");

        file.write("\"" + self.fullName() + "\"" + "|");
        file.write(str(self.thread) + "|");
        file.write(str(self.time) + "|");
        file.write(str(duration) + "\n");

    def writeToFile(self, file):
        if (self.op == "enter"):
            file.write("-->");
        elif (self.op == "exit"):
            file.write("<--");
        else:
            file.write(self.op);
        file.write(separator + self.func + separator + str(self.thread) +
                       separator + str(self.time));
        if (self.otherInfo is not None):
            file.write(separator + self.otherInfo);

#
# LockRecord contains temporary information for generating lock-held times

class LockRecord:

    def __init__(self, name, fname, thread, timeAcquired):
        self.name = name;
        self.funcName = fname;
        self.thread = thread;
        self.timeAcquired = long(timeAcquired);

    def printLockRecord(self):
        print(self.name + ": [" + str(self.thread) + "] " +
              str(self.timeAcquired) + "\n");

#
# A pattern is a complete callstack and its metadata: how many
# times it was encountered and the starting positions in the trace.
#

class Pattern:

    def __init__(self, pattern):
        self.pattern = pattern;
        self.tracePositions = [];
        self.isSingleton = True;

#
# TraceStats class holds attributes pertaining to the performance
# trace.

class TraceStats:
    def __init__(self, name):
        self.name = name;
        self.startTime = 0;
        self.endTime = 0;

    def setStartTime(self, startTime):
        self.startTime = startTime;

    def setEndTime(self, endTime):
        self.endTime = endTime;

    def getTotalTime(self):
        if (self.startTime == 0 or self.endTime == 0):
            print("Warning: start or end time not set for trace " +
                   self.name);
        return self.endTime - self.startTime;
#
# PerfData class contains informtation about the function running
# times.

class PerfData:
    def __init__(self, name, funcName, otherInfo, threadID):
        global treatLocksSpecially;

        self.name = name;
        self.originalName = funcName;
        if shortenFuncName and (self.originalName in shortnameMappings):
            self.originalName = shortnameMappings[self.originalName]
        # If this is a lock function, then otherInfo
        # would contain the information for identifying
        # this lock.
        #
        if (treatLocksSpecially):
            self.lockName = otherInfo;
        self.threadID = threadID;
        self.numCalls = 0;
        self.totalRunningTime = long(0);
        self.runningTimes = [];
        self.maxRunningTime = 0;
        self.maxRunningTimeTimestamp = 0;
        self.filtered = False;
        self.cumSumSquares = 0.0;

    def update(self, runningTime, beginTime):
        global outliersFile;

        self.totalRunningTime = self.totalRunningTime + runningTime;
        self.numCalls = self.numCalls + 1;

        if (runningTime > self.maxRunningTime):
            self.maxRunningTime = runningTime;
            self.maxRunningTimeTimeStamp = beginTime;

        # Update cumulative variance, so we can signal outliers
        # on the fly.
        #
        cumMean = float(self.totalRunningTime) / float(self.numCalls);
        self.cumSumSquares = self.cumSumSquares + \
          math.pow(float(runningTime) - cumMean, 2);

        if (outliersFile is not None):
            if (runningTime > cumMean + 2 * self.getStandardDeviation()):
                outliersFile.write("T" + str(self.threadID) + ": " + self.name
                                       + " took "
                                       + str(runningTime) +
                                       " ns at time " + str(beginTime) + "\n");

    def getAverage(self):
        return (float(self.totalRunningTime) / float(self.numCalls));

    def getStandardDeviation(self):
        return math.sqrt(self.cumSumSquares / float(self.numCalls));

    def printSelf(self, file):
        if(file is None):
            file = sys.stdout;

        file.write("*** " + self.name + "\t" +
                   str(self.numCalls) + "\t" + str(self.totalRunningTime) + "\t"
                   + str(self.getAverage()) + "\n");
        file.write("\t Total running time: " +
                   '{:,}'.format(self.totalRunningTime) +
                   " ns.\n");
        file.write("\t Average running time: "
              + '{:,}'.format(long(self.getAverage())) + " ns.\n");
        file.write("\t Largest running time: " +
                   '{:,}'.format(self.maxRunningTime) +
               " ns.\n");

    def printSelfCSVLine(self, file):
        if(file is None):
            file = sys.stdout

        file.write("{}, {}, {}, {}, {}\n"
                   .format(self.name, self.numCalls, self.totalRunningTime,
                           self.getAverage(), self.maxRunningTime))

    def printSelfHTML(self, prefix, locksSummaryRecords):
        with open(prefix + "/" + self.name + ".txt", 'w+') as file:
            file.write(self.name + "\n");
            file.write("\t Original full name: " + self.originalName + "\n");
            file.write("\t Total running time: " +
                       '{:,}'.format(self.totalRunningTime) +
                       " ns.\n");
            file.write("\t Number of invocations: " +
                        '{:,}'.format(self.numCalls) +
                       ".\n");
            file.write("\t Average running time: "
                        + '{:,}'.format(long(self.getAverage())) + " ns.\n");
            file.write("\t Standard deviation: "
                           + '{:,}'.format(self.getStandardDeviation()) + "\n");
            file.write("\t Largest running time: " +
                           '{:,}'.format(self.maxRunningTime) +
                           " ns.\n");
            file.write("------------------\n");
            if (treatLocksSpecially):
                if (self.lockName is not None):
                    if (self.lockName in locksSummaryRecords):
                        lockData = locksSummaryRecords[self.lockName];
                        lockData.printSelfHTML(file);


#
# LockData class contains information about lock-related functions

class LockData:

    def __init__(self, name):
        self.name = name;
        self.numAcquire = 0;
        self.numRelease = 0;
        self.numTryLock = 0;
        self.timeAcquire = 0;
        self.timeTryLock = 0;
        self.timeRelease = 0;
        self.timeHeld = 0;
        self.lastAcquireRecord = None;
        self.lockHeldTimes = [];

    def getAverageAcquire(self):
        if(self.numAcquire > 0):
            return (float(self.timeAcquire) / float(self.numAcquire));
        else:
            return 0;

    def getAverageRelease(self):
        if(self.numRelease > 0):
            return (float(self.timeRelease) / float(self.numRelease));
        else:
            return 0;

    def getAverageTryLock(self):
        if(self.numTryLock > 0):
            return (float(self.timeTryLock) / float(self.numTryLock));
        else:
            return 0;

    def getAverageTimeHeld(self):
        if(self.numRelease > 0):
            return (float(self.timeHeld) / float(self.numRelease));
        else:
            return 0;

    def printSelf(self, file):
        if (file is None):
            file = sys.stdout;

        file.write("Lock \"" + self.name + "\":\n");
        file.write("\t Num acquire: " + str(self.numAcquire) + "\n");
        file.write("\t Num trylock: " + str(self.numTryLock) + "\n");
        file.write("\t Num release: " + str(self.numRelease) + "\n");
        file.write("\t Average time in acquire: "
              + str(long(self.getAverageAcquire())) + " ns.\n");
        file.write("\t Average time in trylock: "
              + str(long(self.getAverageTryLock())) + " ns.\n");
        file.write("\t Average time in release: "
              + str(long(self.getAverageRelease())) + " ns.\n");
        file.write("\t Average time the lock was held: "
              + str(long(self.getAverageTimeHeld())) + " ns.\n");

    def printSelfHTML(self, file):

        file.write("Lock \"" + self.name + "\":\n");
        file.write("\t Num acquire: " + str(self.numAcquire) + "\n");
        file.write("\t Num trylock: " + str(self.numTryLock) + "\n");
        file.write("\t Num release: " + str(self.numRelease) + "\n");
        file.write("\t Average time in acquire: "
              + str(long(self.getAverageAcquire())) + " ns.\n");
        file.write("\t Average time in trylock: "
             + str(long(self.getAverageTryLock())) + " ns.\n");
        file.write("\t Average time in release: "
              + str(long(self.getAverageRelease())) + " ns.\n");
        file.write("\t Average time the lock was held: "
              + str(long(self.getAverageTimeHeld())) + " ns.\n");



def mem():
    print('Memory usage         : % 2.2f MB' % round(
        resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024.0/1024.0,1)
    )

#
# The following data structures and functions help us decide what
# kind of lock-related action the function is doing:
# acquiring the lock, releasing the lock, of trying to acquire the lock.
#

acquireStrings = ["acquire", "lock"];
trylockStrings = ["trylock"];
releaseStrings = ["release", "unlock"];

def looks_like_acquire(funcname):

    if(looks_like_release(funcname)):
        return False;
    if(looks_like_trylock(funcname)):
        return False;

    for hint in acquireStrings:
        if(funcname.find(hint) != -1):
            return True;
    return False;

def looks_like_trylock(funcname):

    for hint in trylockStrings:
        if(funcname.find(hint) != -1):
            return True;
    return False;


def looks_like_release(funcname):

    for hint in releaseStrings:
        if(funcname.find(hint) != -1):
            return True;
    return False;

def looks_like_lock(funcname):

    if ("block" in funcname):
        return False;
    if (looks_like_acquire(funcname) or
        looks_like_release(funcname) or
        looks_like_trylock(funcname)):
        return True;
    else:
        return False;

def do_lock_processing(locksDictionary, logRec, runningTime,
                       lockName):
    global multipleAcquireWithoutRelease;
    global noMatchingAcquireOnRelease;
    global tryLockWarning;
    global verbose;

    func = logRec.func

    if(not locksDictionary.has_key(lockName)):
        lockData = LockData(lockName);
        locksDictionary[lockName] = lockData;

    lockData = locksDictionary[lockName];
    lastAcquireRecord = lockData.lastAcquireRecord;

    # If this is an acquire or trylock, simply update the stats in the
    # lockData object and remember the lastAcquire record, so we can
    # later match it with a corresponding lock release.
    #
    # If this is a release, update the stats in the lockData object and
    # get the corresponding acquire or trylock so we can compute the lock
    # held time.
    #
    if(looks_like_acquire(func) or looks_like_trylock(func)):

        lockRec = LockRecord(lockName, func, logRec.thread, logRec.time);

        if(looks_like_acquire(func)):
            if(lastAcquireRecord is not None):
                if(verbose):
                    print("Another acquire record seen on acquire. "
                          " for lock " + lockName);
                    print("Current lock record:");
                    lockRec.printLockRecord();
                    print("Existing acquire record:");
                    lastAcquireRecord.printLockRecord();
                multipleAcquireWithoutRelease = multipleAcquireWithoutRelease \
                                                + 1;
            else:
                lockData.lastAcquireRecord = lockRec;

            lockData.numAcquire = lockData.numAcquire + 1;
            lockData.timeAcquire = lockData.timeAcquire + runningTime;
        elif(looks_like_trylock(func)):
            if(lastAcquireRecord is not None):
                if(lastAcquireRecord.funcName != func):
                    if(verbose):
                        print("Warning: A trylock record seen, but not in the "
                              "same function as ours!");
                        print("Current lock record:");
                        lockRec.printLockRecord();
                        print("Existing acquire record:");
                        lastAcquireRecord.printLockRecord();
                    tryLockWarning = tryLockWarning + 1;
                else:
                    # If there is already an acquire record with the same func
                    # name as ours, this means that the lock was not acquired in
                    # the last try attempt. We update the timestamp, so that
                    # lock held time is subsequently calculated correctly.
                    lastAcquireRecord.timeAcquired = logRec.time;
            else:
                lockData.lastAcquireRecord = lockRec;

            lockData.numTryLock = lockData.numTryLock + 1;
            lockData.timeTryLock = lockData.timeTryLock + runningTime;
        else:
            print("PANIC!")
            sys.exit(-1);

    elif(looks_like_release(func)):

        if(lastAcquireRecord is None):
            if(verbose):
                print("Could not find a matching acquire for: ")
                logRec.printLogRecord();
                print("Lock name: " + lockName);
            noMatchingAcquireOnRelease = noMatchingAcquireOnRelease + 1;
        else:
            lockHeldTime = logRec.time - lastAcquireRecord.timeAcquired;
            lockData.timeHeld = lockData.timeHeld + lockHeldTime;
            lockData.lockHeldTimes.append(long(lockHeldTime));

            # Reset the lockAcquire record to null
            lockData.lastAcquireRecord = None;

        lockData.numRelease = lockData.numRelease + 1;
        lockData.timeRelease = lockData.timeRelease + runningTime;

    else:
        print("PANIC! Unrecognized lock function: " + func);
        sys.exit(-1);


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

    # To generate colours from red to pale green, use:
    # baseHue = 360;
    # lightness = 0.56
    # lightInc = 0.02
    #
    # In the loop: baseHue - i * 20.
    #
    colorRange = [];
    baseHue = 200;
    saturation = 0.70;
    lightness = 0.4;
    lightInc = 0.04;

    for i in range(0, 14):
        hslColor = HSL(baseHue, saturation, lightness + lightInc * i,);
        hexColor = hslColor.toHex();
        colorRange.append(hexColor);

    return colorRange;

def extractFuncName(nodeName):

    words = nodeName.split(" ");

    if (words[0] == "enter" or words[0] == "exit"):
        return " ".join(words[1:len(words)]);
    else:
        return nodeName;
#
# Figure out the percent execution time for each function relative to the total.
# Compute the colour based on the percent. Set the node colour accordingly.
# Update the node label with the percent value.
#
def augment_graph(graph, funcSummaryData, traceStats, prefix, htmlDir):

    # This dictionary is the mapping between function names and
    # their percent of execution time.
    #
    percentDict = {};

    # This is the dictionary of function names with colour codes
    # based on their contribution to the total runtime.
    #
    funcWithColorCode = {};

    # Generate a progression of colours from bright red to pale green
    #
    rgbArray = buildColorList();

    # Generate a dictionary keyed by function name, where the value is
    # the percent runtime contributed to total by this function.
    #
    traceRuntime = traceStats.getTotalTime();
    for func, pdr in funcSummaryData.items():
        if(pdr.filtered):
            continue;
        percent = float(pdr.totalRunningTime) / float(traceRuntime) * 100;
        percentDict[func] = percent;

    # Sort the dictionary by percent. We get back a list of tuples.
    #
    sortedByPercentRuntime = sorted(percentDict.items(),
                                    key=operator.itemgetter(1));

    # Look up the colour for each function based on its contribution
    # to the total runtime. Greater contribution --> more intense color.
    #
    for funcPercentTuple in reversed(sortedByPercentRuntime):
        func = funcPercentTuple[0];
        percent = funcPercentTuple[1];
        percentStr = str(round(percent)) + "%";

        # Let's find the color for this percent value.
        #
        idx = int(round((100.0 - percent) / 7.5));
        funcWithColorCode[func] = [rgbArray[idx], percentStr];

    for func, attrs in funcWithColorCode.items():

        if graphType == 'func_only':
            allNames = [func];
        else:
            enterNodeName = "enter " + func;
            exitNodeName  = "exit " + func;
            allNames = [enterNodeName, exitNodeName];

        for nodeName in allNames:
            graph.node[nodeName]['label'] = nodeName + "\n" + \
                                             attrs[1];
            graph.node[nodeName]['style'] = "filled, rounded";
            graph.node[nodeName]['color'] = attrs[0];
            graph.node[nodeName]['URL'] = "_" + prefix.upper() \
              + "/" + extractFuncName(nodeName) + ".txt";

def update_graph(graph, nodeName, prevNodeName):

    global totalNodes;

    if (not graph.has_node(nodeName)):
            graph.add_node(nodeName, fontname="Helvetica");
            graph.node[nodeName]['shape'] = 'box';
            totalNodes += 1;

    if (not graph.has_edge(prevNodeName, nodeName)):
        graph.add_edge(prevNodeName, nodeName, label = " 1 ",
                       fontname="Helvetica");
    else:
        graph[prevNodeName][nodeName]['label'] = \
            " " + str(int(graph[prevNodeName][nodeName]['label']) + 1) + " ";

    if(prevNodeName == "START"):
        graph[prevNodeName][nodeName]['label'] = "";
        if (graphType == 'func_only'):
            graph[prevNodeName][nodeName]['label'] = " 1 "

def generate_func_only_graph(graph, logRecords, prevNodeName):

    funcStack = [prevNodeName];
    lastFuncName = prevNodeName;

    for logRec in logRecords:
        if logRec.op == 'enter':
            update_graph(graph, logRec.func, lastFuncName)
            funcStack.append(logRec.func)
        elif logRec.op == 'exit':
            if funcStack[-1] == logRec.func:
                lastFuncName = funcStack.pop()

    return lastFuncName;

def generate_graph(logRecords):

    global totalNodes;
    totalNodes = 0;

    graph = nx.DiGraph();

    graph.add_node("START", fontname="Helvetica");
    graph.node["START"]['shape']='box'
    prevNodeName = "START";

    if graphType == 'func_only':
        prevNodeName = generate_func_only_graph(graph, logRecords, prevNodeName)
    else:
        for logRec in logRecords:
            if (logRec.filtered):
                continue;
            nodeName = logRec.op + " " + logRec.fullName();
            update_graph(graph, nodeName, prevNodeName);
            prevNodeName = nodeName;

    graph.add_node("END", fontname="Helvetica");
    graph.add_edge(prevNodeName, "END");
    graph.node["END"]['shape']='diamond';

    print("Generated a FlowViz graph with " + str(totalNodes) + " nodes.");
    return graph;


def decideWhichFuncsToFilter(funcSummaryRecords, traceStats):

    global percentThreshold;
    traceRuntime = traceStats.getTotalTime();

    if (percentThreshold == 0.0):
        return;

    for key, pdr in funcSummaryRecords.items():
        percent = float(pdr.totalRunningTime) / float(traceRuntime) * 100;

        if (percent <= percentThreshold):
            pdr.filtered = True;


def transform_name(name, transformMode, CHAR_OPEN=None, CHAR_CLOSE=None):
    if transformMode == 'multiple lines':
        lineLength = 50
        lines = []
        i = 0
        while len(name) > lineLength:
            if i == 0:
                lines.append(name[0:lineLength])
            else:
                lines.append(name[0:lineLength])
            name = name[lineLength:]
            i += 1
        lines.append(name)
        return '\n'.join(lines)
    elif transformMode == 'replace with *':
        stack = []
        chars = []
        for c in name:
            if c == CHAR_OPEN:
                if len(stack) == 0:
                    chars.append(c)
                stack.append(c)
            elif c == CHAR_CLOSE:
                if len(stack) == 0: # miss the matched '<'
                    chars.append(c)
                else:
                    stack.pop()
                    if len(stack) == 0:
                        chars.append('*')
                        chars.append(CHAR_CLOSE)
            else:
                if len(stack) == 0:
                    chars.append(c)

        return ''.join(chars)
    else:
        return name


shortnameMapped = {}   # originalName     => shortname
shortnameMappings = {} # shortname      => originalName
shortnameVersion = {}  # shortnameBase  => version

# Different functions could have the same short name.
# The following method is to generate unique short names for
# different functions by appending _v* to the generated short name
#
def unique_shortname(originalName):

    if originalName in shortnameMapped:
        return shortnameMapped[originalName];

    shortnameBase = transform_name(originalName, 'replace with *', '<', '>');
    shortnameBase = transform_name(shortnameBase, 'replace with *', '(', ')');
    version = 0;

    if (shortnameBase in shortnameVersion):
        version = shortnameVersion[shortnameBase];
    shortnameVersion[shortnameBase] = version + 1;

    shortname = shortnameBase;
    if (version != 0):
        shortname = shortnameBase + "_v" + str(version)

    shortnameMapped[originalName] = shortname;
    shortnameMappings[shortname] = originalName;
    return shortname;

def dump_shortname_maps(filename):
    with open(filename, 'w') as fp:
        json.dump(shortnameMappings, fp);


def generatePerFuncHTMLFiles(prefix, htmlDir,
                                 funcSummaryRecords, locksSummaryRecords):

    dirname = htmlDir + "/" + "_" + prefix.upper();

    if not os.path.exists(dirname):
        try:
            os.mkdir("./" + dirname);
            print(color.BOLD + prefix + ": " +  color.END +
                  "Directory " + dirname + " created");
        except:
            print("Could not create directory " + dirname);
            return;

    for pdr in funcSummaryRecords.values():
        if (not pdr.filtered):
             pdr.printSelfHTML(dirname, locksSummaryRecords);

# In some cases we need to strip the HTML directory name from the
# beginning of the imageFileName, because the image source
# must be relative to the html file, which itself is in
# the HTML directory.
#
def stripHTMLDirFromFileName(fileName, htmlDir):

    if (fileName.startswith(htmlDir)):
        fileName = fileName[len(htmlDir):];

    while (fileName.startswith("/")):
        fileName = fileName[1:];

    return fileName;

def insertIntoTopHTML(imageFileName, htmlFileName, topHTMLFile):

    global htmlTemplate;

    # Extract thread ID from the file names. We assume that this
    # is the first number encountered in the file name.
    #
    numbers = re.findall(r'\d+', imageFileName);
    if (len(numbers) > 0):
        threadID = str(numbers[0]);
    else:
        threadID = "";

    # Read the file, find the placeholder patterns, replace them
    # with the actual values. Write the text into top HTML file.
    for line in htmlTemplate:
        if ("#Thread" in line):
            line = line.replace("#Thread", "Thread " + threadID);
        if ("#htmlFile" in line):
            line = line.replace("#htmlFile", htmlFileName);
        if ("#imageFile" in line):
            line = line.replace("#imageFile", imageFileName);
        topHTMLFile.write(line);

    # Rewind the template file for the next reader
    htmlTemplate.seek(0);


def generatePerFileHTML(htmlFileName, imageFileName, mapFileName, htmlDir,
                            topHTMLFile):
    i = 0;

    try:
        htmlFile = open(htmlFileName, "w");
    except:
        print("Could not open " + htmlFileName + " for writing");
        return;

    try:
        mapFile = open(mapFileName, "r");
    except:
        print("Could not open " + mapFileName + " for writing");
        return;

    relativeImageFileName = stripHTMLDirFromFileName(imageFileName, htmlDir);

    htmlFile.write("<html><img src=\"" + relativeImageFileName +
                       "\"  usemap=\"#G\">\n");
    htmlFile.write("<map id=\"G\" name=\"G\">\n");

    for line in mapFile:
        i = i + 1;
        if (i == 1):
            assert(line.startswith("<map id="));
            continue;

        htmlFile.write(line);

    htmlFile.write("</html>\n");

    htmlFile.close();
    mapFile.close();

def generateTopHTML(filenames, htmlDir):

    topHTMLFile = createTopHTML(htmlDir);

    if (topHTMLFile is None):
        return;

    # This list will keep track of the trace files, whose images we
    # already added to the top HTML file, so we don't add the same
    # file twice. A user may specify the same file more than once
    # on the command line, because two different file names may
    # contain the same prefix. We are using the prefix to derive
    # image and HTML file names.
    #
    alreadyAdded = [];

    # Iterate over the list of files. Extract the prefix, construct
    # the desired image and HTML file names based on global variables
    # that were set from the command-line arguments, emit HTML into
    # topHTMLFile.
    #
    for fname in filenames:
        prefix = getPrefix(fname);
        if (prefix in alreadyAdded):
            continue;
        else:
            alreadyAdded.append(prefix);

        imageFileName = prefix + "." + graphType + "." + \
          str(percentThreshold) + "." + graphFilePostfix;
        htmlFileName = prefix + "." + graphType + "." + \
          str(percentThreshold) + ".html";

        insertIntoTopHTML(imageFileName, htmlFileName, topHTMLFile);

    return topHTMLFile;

def funcFiltered(func, funcSummaryRecords):

    if not funcSummaryRecords.has_key(func):
        print("Warning: no performance record for function " +
                  func);
        return False;

    funcPDR = funcSummaryRecords[func];
    if (funcPDR.filtered):
        return True;
    else:
        return False;

def parseLogRecsFromDBFile(prefix, dbFile, funcSummaryRecords,
                           totalRecordsExpected):

    global totalNodes;

    filteredLogRecords = [];
    prevNodeName = "START";
    totalNodes = 0;
    totalProcessed = 0l;

    graph = nx.DiGraph();
    graph.add_node("START", fontname="Helvetica");
    graph.node["START"]['shape']='box';

    while True:
        otherInfo = None;
        fullName = None;

        line = dbFile.readline();
        if (line is None):
            break;
        if (line == ''):
            break;

        totalProcessed += 1;
        if (totalProcessed > totalRecordsExpected):
           print("Warning: processing more than expected: " +
                 str(totalProcessed) + " vs " + str(totalRecordsExpected));
           print("Will stop processing.");
           break;

        words = line.split("|");
        if (len(words) < 6):
            print("Invalid record format in SQL file. " +
                      "Your results may be incorrect.");
            print(line);
            continue;

        if (words[1] == "0"):
            op = "enter";
        elif (words[1] == "1"):
            op = "exit";
        else:
            print("Invalid record format in SQL file. " +
                       "Your results may be incorrect.");
            print(line);
            continue;

        func = words[2].strip('"');

        # Let's see if we need this log record
        if (funcFiltered(func, funcSummaryRecords)):
            continue;
        else:
            nodeName = op + " " + func;
            update_graph(graph, nodeName, prevNodeName);
            prevNodeName = nodeName;

    graph.add_node("END", fontname="Helvetica");
    graph.add_edge(prevNodeName, "END");
    graph.node["END"]['shape']='diamond';

    print(color.BOLD + prefix + ": " +  color.END +
          "Generated a FlowViz graph with " + str(totalNodes) + " nodes.");
    return graph;

# We don't properly support this use case.
# Return 0, meaning that we can't put the resulting
# sub-traces into the final trace.sql, as their internal
# IDs will clash.
#
def getNewIDForText(fname, lastUsedID):

    command = [];
    numRecords = 0;

    # Find out the number of lines in the file
    try:
        command.append("wc");
        command.append("-l");
        command.append(fname);
        x = subprocess.check_output([command]);
        numRecords = int(x);
    except:
        print(color.RED + color.BOLD);
        print("Warning: could not find the number of lines in " + fname +
              " using command \'" + str(command) + "\'");
        print(color.END);

    return lastUsedID + numRecords;

traceRecordSize = 0;

def getNewIDForBinary(fname, lastUsedID):

    global traceRecordSize;

    if (traceRecordSize == 0):
        # Try to query the trace parser
        #try:
        try:
            parserLocation = os.environ["DINAMITE_TRACE_PARSER"];
            command = [];
            command.append(parserLocation);
            command.append("-p");
            command.append("fastfunc");
            command.append("-s");
            print(command);
            x = subprocess.check_output(command);
            traceRecordSize = int(x);
            print("Trace record size is " + str(traceRecordSize));
        except:
            # If unsuccessful, assume a reasonable small value
            print(color.RED + color.BOLD);
            print("Warning, could not query the trace parser for the " +
                  "size of the binary record. Assuming 28 bytes.");
            traceRecordSize = 24;
            print(color.END);

    try:
        fsize = os.path.getsize(fname);
        numRecords = fsize / traceRecordSize + 1;
        return lastUsedID + numRecords;
    except:
        return lastUsedID;

lastUsedID = 0;
def getFirstUnusedId(fname):

    global lastUsedID;
    global traceRecordSize;

    oldLastUsedID = lastUsedID;

    if (looksLikeTextTrace(fname)):
        lastUsedID = getNewIDForText(fname, lastUsedID);
    else:
        lastUsedID = getNewIDForBinary(fname, lastUsedID);

    return oldLastUsedID;


currentStackLevel = 0;
currentPattern = [];
def minePatterns(funcName, stackLevel):

    global currentStackLevel;
    global currentPattern;


    funcID = funcNameToID(stackRec.fullName());


    # We are going up a stack level. Let's stash the current pattern.
    # We will use it later once we are back at this stack level.
    #
    if (stackLevel > currentStackLevel):
        if (stackLevel - currentStackLevel > 1 and currentStackLevel != 0):
            print("Warning: jumping up more than one stack level");
            print(funcName + ": stack level is " + str(stackLevel) +
                  ", previous stack level was " + str(currentStackLevel));
            return;

        # Stash the current pattern
        if (len(currentPattern) > 0):
            runningPatternForLevel[currentStackLevel] = currentPattern;
            currentPattern = [];

    # We have encountered a completed function at the same level as
    # we were previously. Let's see if we can compress the remembered
    # pattern for the current level on the fly.
    #
    if (stackLevel == currentStackLevel):
        currentPattern.append(funcID);
        currentPattern = compressAndReencode(currentPattern);

    # We are going down the stack level. This means that the parent of
    # the completed functions we have just processed has completed.
    # Let's record the pattern we derived and retrieve the pattern for
    # the new stack level.
    #
    if (stackLevel < currentStackLevel):
        if (currentStackLevel - stackLevel > 1):
            print("Warning: jumping down more than one stack level");
            print(funcName + ": stack level is " + str(stackLevel) +
                  ", previous stack level was " + str(currentStackLevel));
            return;

        childPattern = finalizeCurrentPattern(currentPattern);
        currentStackLevel = stackLevel;

        if (runningPatternForLevel.has_key(currentStackLevel)):
            currentPattern = runningPatternForLevel[currentStackLevel];
            if (currentPattern is None):
                print("Warning: retrieved a null current pattern");
            if (len(currentPattern) == 0):
                print("Warning: retrieved a current pattern of zero length");
        else:
            currentPattern = [];

        currentPattern.append(funcID);
        currentPattern.append(childPattern);
        currentPattern = compressAndReencode(currentPattern);




def parse_file(traceFile, prefix, createTextFile, firstUnusedID):

    global dbFile;
    global htmlDir;
    global summaryCSV;
    global summaryTxt;
    global treatLocksSpecially;

    endTime = 0;
    fileBeginPosition = 0l;
    fileEndPosition = 0l;
    funcSummaryRecords = {};
    graph = nx.DiGraph();
    lockStack = [];
    locksSummaryRecords = {}
    outputFile = None;
    recID = firstUnusedID;
    traceStats = TraceStats(prefix);
    totalRecordsWritten = 0;
    stack = [];
    startTime = 0;
    tempDBFileName = prefix + ".sql";

    graph.add_node("START", fontname="Helvetica");
    graph.node["START"]['shape']='box'
    prevNodeName = "START";

    try:
       dbFile = open(tempDBFileName, "w+");
    except:
       print("Could not open " + tempDBFileName + " for reading and writing.");
       return;

    print(color.BOLD + prefix + ": " +  color.END +
          "Saving data to file " + tempDBFileName);

    if (createTextFile):
        try:
            outputFile = open(prefix + ".txt", "w");
        except:
            print("Could not open " + prefix + ".txt for writing.");
            # We will not exit on this error, but will attempt to
            # parse the trace anyway.

    while True:
        line = traceFile.readline();

        if (line is None):
            break;
        if (line == ''):
            break;

        words = line.split(separator);
        thread = 0;
        time = 0;
        func = "";
        otherInfo = None;

        if(len(words) < 4):
           continue;

        try:
            func = words[1];
            if shortenFuncName:
                func = unique_shortname(func)
            thread = int(words[2]);
            time = long(words[3]);
            if (len(words) > 4):
                parts = words[4:len(words)];
                otherInfo = (" ".join(parts)).rstrip();

        except ValueError:
            print("Could not parse: " + line);
            continue;

        if (words[0] == "-->"):
            op = "enter";
        elif (words[0] == "<--"):
            op = "exit";
        else:
            continue;

        rec = LogRecord(func, op, thread, time, otherInfo);

        if(startTime == 0):
            startTime = time;
        else:
            endTime = time;

        if(op == "enter"):
            # Timestamp for function entrance
            # Push each entry record onto the stack.
            stack.append(rec);

            # This is a new enter record, so generate an id for it.
            rec.setID(recID);
            recID = recID + 1;

            if (dbFile is not None):
                rec.writeToDBFile(dbFile, 0);
                totalRecordsWritten += 1;

            # If we are told to write the records to the output
            # file, do so.
            if(outputFile is not None):
                rec.writeToFile(outputFile);
                outputFile.write("\n");

        else:
            if(outputFile is not None):
                # If this is a function exit record, we may need to add
                # otherInfo to the end of the line. otherInfo contains
                # function arguments, so it is only available at function
                # entry.
                # So for now we write the line without the newline character
                # at the end. Later we will either add the otherInfo with the
                # newline character (if this information was provided with the
                # function entry record, or just the newline character
                # otherwise.
                #
                rec.writeToFile(outputFile);

            found = False;

            # Timestamp for function exit. Find its
            # corresponding entry record by searching
            # the stack.
            while(len(stack) > 0):
                stackRec = stack.pop();
                if(stackRec is None):
                    print("Ran out of opening timestamps when searching "
                          "for a match for: " + line);
                    break;

                # If the name of the entrance record
                # on the stack is not the same as the name
                # in the exit record we have on hand, complain
                # and continue. This means that there are errors
                # in the instrumentation, but we don't want to fail
                # because of them.
                if(not (stackRec.func == rec.func)):
                    continue;
                else:
                    # We have a proper function record. Let's add the data to
                    # the file's dictionary for this function.

                    runningTime = long(rec.time) - long(stackRec.time);

                    if(not funcSummaryRecords.has_key(stackRec.fullName())):
                        newPDR = PerfData(stackRec.fullName(), stackRec.func,
                                              stackRec.otherInfo, thread);
                        funcSummaryRecords[stackRec.fullName()] = newPDR;

                    pdr = funcSummaryRecords[stackRec.fullName()];
                    pdr.update(runningTime, stackRec.time);
                    found = True;

                    # Full name is the name of the function, plus whatever other
                    # info was given to us, usually values of arguments. This
                    # information is only printed for the function entry record,
                    # so if we are at the function exit record, we must copy
                    # that information from the corresponding entry record.
                    #
                    rec.otherInfo = stackRec.otherInfo;
                    rec.setID(stackRec.id);

                    minePatterns(stackRec.fullName(), len(stack));

                    # Now that we know this function's duration we can write
                    # it's opening and closing record into the database
                    # importable file.
                    #
                    if (dbFile is not None):
                        rec.writeToDBFile(dbFile, runningTime);
                        totalRecordsWritten += 1;

                    # If this is a lock-related function, do lock-related
                    # processing. stackRec.otherInfo variable would contain
                    # the name of the lock, since only the function enter
                    # record has this information, not the exit record.
                    if (treatLocksSpecially and stackRec.otherInfo is not None
                                and looks_like_lock(func)):
                            do_lock_processing(locksSummaryRecords, rec,
                                        runningTime, stackRec.otherInfo);

                    if(stackRec.otherInfo is not None and
                               outputFile is not None):
                            outputFile.write(separator + stackRec.otherInfo);
                    break;
            if (not found):
                print("Could not find matching function entrance for line: \n"
                      + line);

            if(outputFile is not None):
                outputFile.write("\n");

    traceStats.setStartTime(startTime);
    traceStats.setEndTime(endTime);

    if (dbFile is not None):
       dbFile.flush();

    if (outputFile is not None):
        outputFile.close();

    print(color.BOLD + prefix + ": " +  color.END +
          "Wrote " + str(totalRecordsWritten) + " records to " +
          tempDBFileName);

    if (summaryTxt):
        generateSummaryFile('.txt', prefix, traceStats, funcSummaryRecords,
                                locksSummaryRecords)
    if (summaryCSV):
        generateSummaryFile('.csv', prefix, traceStats, funcSummaryRecords,
                                locksSummaryRecords)

    # Re-read the records from the DB file, filtering the ones not needed for
    # the graph. By re-reading them from the file as opposed to keeping the
    # records and filtering them in memory we dramatically reduce the size
    # of the virtual address space and prevent out-of-memory errors for very
    # large files.
    #
    print(color.BOLD + prefix + ": " +  color.END +
          "Filtering records based on performance criteria...");
    decideWhichFuncsToFilter(funcSummaryRecords, traceStats);

    # Re-parse the needed records and generate the graph
    dbFile.seek(0, 0);
    graph = parseLogRecsFromDBFile(prefix, dbFile, funcSummaryRecords,
                                                totalRecordsWritten);
    dbFile.close();

    # Augment graph attributes to reflect performance characteristics
    augment_graph(graph, funcSummaryRecords, traceStats, prefix, htmlDir);

    # Prepare the graph
    aGraph = nx.drawing.nx_agraph.to_agraph(graph);
    aGraph.add_subgraph("START", rank = "source");
    aGraph.add_subgraph("END", rank = "sink");

    # Generate the dot file
    nameNoPostfix = htmlDir + "/" + \
      prefix + "." + graphType + "."+ str(percentThreshold) + "."

    dotFileName = nameNoPostfix + "dot";

    print(color.BOLD + prefix + ": " +  color.END +
          "Writing dot file to: " + dotFileName + " ... ");
    try:
        aGraph.write(dotFileName);
    except:
        print(color.RED + color.BOLD);
        print("Could not write dot file " + dotFileName);
        print sys.exc_info()[0];
        print sys.exc_info()[1];
        print sys.exc_info()[2];
        print(color.END);

    # Dumping original function names if names were shortened
    if shortenFuncName:
        shortnameMapsFilename = 'shortname_maps.{}.json'.format(prefix)
        dump_shortname_maps(shortnameMapsFilename)

    # Generate HTML files summarizing function stats for all functions that
    # were not filtered.
    print(color.BOLD + prefix + ": " +  color.END +
          "Generating per-function HTML file...");
    generatePerFuncHTMLFiles(prefix, htmlDir,
                                 funcSummaryRecords, locksSummaryRecords);

    return totalRecordsWritten;

def generateImageAndHTMLFilesFromDot(prefix, topHTMLFile):

    global graphType;
    global htmlDir;
    global percentThreshold;

    nameNoPostfix = htmlDir + "/" + \
      prefix + "." + graphType + "."+ str(percentThreshold) + "."

    dotFileName = nameNoPostfix + "dot";

    try:
        imageFileName = nameNoPostfix + graphFilePostfix;
        mapFileName = nameNoPostfix + "cmapx";

        print("Saving graph image to: " + imageFileName + "... "),
        ret = os.system("dot -Tpng " + dotFileName + " > " + imageFileName);
        if (ret == 0):
            print("Success!");
        else:
            print("Failed...");

        print("Saving image map to: " + mapFileName + "... "),
        ret = os.system("dot -Tcmapx " + dotFileName + " > " + mapFileName);
        if (ret == 0):
            print("Success!");
        else:
            print("Failed...");

        generatePerFileHTML(nameNoPostfix + "html", imageFileName, mapFileName,
                                htmlDir, topHTMLFile);
    except:
        print(color.RED + color.BOLD);
        print sys.exc_info()[0];
        print sys.exc_info()[1];
        print sys.exc_info()[2];
        print(color.END);

def subprocessParse(fname, recsProcessed, firstUnusedID):

    global htmlDir;
    global generateTextFiles;
    global totalRecords;

    retTuple = (0, 0);
    prefix = getPrefix(fname);

    print(color.BOLD + color.BLUE +
          "Processing file with prefix " + prefix + color.END);

    # If this is a text trace, we simply parse the file.
    # If this is a binary trace we spawn a subprocess to
    # convert the text to binary and read the stdout of
    # the child process.
    #
    if (looksLikeTextTrace(fname)):
        try:
            traceFile = open(fname, "r");
        except:
            print("Could not open " + fname + " for reading");
            return;

        recs = parse_file(traceFile, prefix, False,
                                      firstUnusedID);

    else:
        # Figure out the name of the script that will launch
        # the binary-to-text converter.
        #
        argsList = getTextConverterCommand();

        if (argsList is None):
            sys.exit();
        # Append the file to the argument list and
        # create the subprocess
        #
        argsList.append(fname);
        process = subprocess.Popen(argsList,
                                       stdout=subprocess.PIPE);
        if (process is None):
            print("Could not create a process from arguments: "
                      + str(argsList));
            sys.exit();

        # Parse the file, reading from the standard out of the
        # created process. That process will output text trace
        # into its standard out.
        #
        recs = parse_file(process.stdout, prefix,
                                  generateTextFiles, firstUnusedID);

    recsProcessed.value = recs;


def generateSummaryFile(fileType, prefix, traceStats, funcSummaryRecords,
                            locksSummaryRecords):
    # Write the summary to the output file.
    try:
        summaryFileName = prefix + ".summary" + fileType;
        summaryFile = open(summaryFileName, "w");
    except:
        print(color.BOLD + prefix + ": " +  color.END +
            "Could not create summary file " + summaryFileName);
        summaryFile = sys.stdout;

    if fileType == '.csv':
        summaryFile.write("Function, Num calls, Total Runtime (ns), "
                              "Averge Runtime (ns), Largest Runtime (ns)\n");
        for fkey, pdr in funcSummaryRecords.items():
            pdr.printSelfCSVLine(summaryFile);
    else:
        summaryFile.write(" SUMMARY FOR FILE " + prefix + ":\n");
        summaryFile.write("------------------------------\n");
        summaryFile.write("Total trace time: "
                      + str(traceStats.getTotalTime()) + "\n");
        summaryFile.write(
            "Function \t Num calls \t Runtime (tot) \t Runtime (avg)\n");

        for fkey, pdr in funcSummaryRecords.items():
            pdr.printSelf(summaryFile);
            summaryFile.write("------------------------------\n");

        lockDataDict = locksSummaryRecords;

        summaryFile.write("\nLOCKS SUMMARY\n");
        for lockKey, lockData in lockDataDict.items():
            lockData.printSelf(summaryFile);

        summaryFile.write("------------------------------\n");

    summaryFile.close();

def getPrefix(fname):

    prefix = re.findall(r'trace.bin.\d+', fname);

    if (len(prefix) > 0):
        return prefix[0];
    else:
        words = fname.split(".txt");
        if (len(words) > 0):
            return words[0];
        else:
            return fname;

def looksLikeTextTrace(fname):

    if (fname.endswith(".txt")):
        return True;
    else:
        return False;

def getTextConverterCommand():

    argsList = [];

    # We need to know where the DINAMITE trace parser lives.
    # Its location should be in the DINAMITE_TRACE_PARSER variable.
    #
    if "DINAMITE_TRACE_PARSER" not in os.environ:
       print("Error: DINAMITE_TRACE_PARSER environment variable MUST be set\n"
             "\t to the location of the trace_parser binary from the\n"
             "\t DINAMITE binary trace toolkit");
       return None;
    parserLocation = os.environ["DINAMITE_TRACE_PARSER"];
    if (parserLocation is None):
        print("Could not determine the location of the DINAMTE " +
                  "binary trace converer trace_parser.");
        print("This script expects to find the location in the " +
                  "DINAMITE_TRACE_PARSER environment variable.");
        return None;

    # Let's make sure that the map files generated by DINAMITE
    # are in the current directory, which is where we expect them
    # to be.
    #
    if not os.path.exists("./map_functions.json"):
        print(color.RED + color.BOLD +
                "Error! Cannot find map_functions.json. Make sure that "
                "this file, generated during DINAMITE compilation, is "
                "in the current working directory." + color.END);
        return None;

    # Things are looking good. We got the location of the parser
    # binary.
    argsList.append(parserLocation);
    argsList.append("-p");
    argsList.append("fastfunc");
    argsList.append("-m");
    argsList.append("./");

    return argsList;

def createHTMLDir(htmlDir):

    if not os.path.exists(htmlDir):
        try:
            os.mkdir("./" + htmlDir);
            print("Directory " + htmlDir + " created");
            return True;
        except:
            print("Could not create directory " + htmlDir);
            return False;


def createTopHTML(htmlDir):

    try:
        topHTML = open(htmlDir + "/index.html", "w");
    except:
        print("Could not open " + htmlDir + "/index.html for writing");
        return None;

    topHTML.write("<!DOCTYPE html>\n");
    topHTML.write("<html>\n");
    topHTML.write("<head>\n");
    topHTML.write("<link rel=\"stylesheet\" type=\"text/css\"" +
                      "href=\"style.css\">\n");
    topHTML.write("</head>\n");
    topHTML.write("<body>\n");

    return topHTML;

def completeTopHTML(topHTML):

    topHTML.write("</body>\n");
    topHTML.write("</html>\n");
    topHTML.close();

def findHTMLTemplate(htmlDir):

    scriptLocation = os.path.dirname(os.path.realpath(__file__));
    htmlTemplateLocation = scriptLocation + "/" + \
      "showGraphs/stateTransitionCharts.html";
    cssFileLocation = scriptLocation + "/" + \
      "showGraphs/style.css";
    if (not (os.path.exists(htmlTemplateLocation) and
                 os.path.exists(cssFileLocation))):
        print("Cannot locate either of the required files: ");
        print("\t" + '\033[1m' + htmlTemplateLocation);
        print("\t" + cssFileLocation);
        print("\033[0m" +
                  "Please make sure you run the script from within the same "
                  + " directory structure as in the original repository.");
        return None;
    else:
        os.system('cp '+ cssFileLocation + " " + htmlDir + "/style.css");

    try:
        htmlTemplate = open(htmlTemplateLocation, "r");
        return htmlTemplate;
    except:
        print("Could not open " + htmlTemplateLocation + " for reading");
        return None;

# Write the top part of the file that has both the commands and data
# to be imported into a SQL database. We use default delimiters for
# MonetDB.
#
def createDBFileHead(dbFile, numRecs):

    # Write the commands to create the schema
    dbFile.write("CREATE TABLE traceTMP (id int, dir tinyint, "
                     "func varchar(255), "
                     "tid smallint, time bigint, duration bigint);\n");

    # Write the command to import the records
    dbFile.write("COPY " + str(numRecs) + " RECORDS INTO traceTMP FROM STDIN "
                 "USING DELIMITERS '|','\\n','\"' NULL AS '';\n");

def createDBFileTail(dbFile):

    global totalRecords;

    # Now create a new table where the original data is sorted
    #
    dbFile.write("CREATE TABLE trace AS SELECT * from traceTMP "
                     "ORDER BY time ASC;\n");
    dbFile.write("DROP TABLE traceTMP;\n");

    # Next, create the table with average function durations and their standard
    # deviations.
    dbFile.write("CREATE TABLE avg_stdev AS SELECT func, "
                    "stddev_pop(duration) AS stdev, avg(duration) AS avg "
                    "FROM trace WHERE trace.dir = 1 GROUP BY func;\n");

    # Create a table with outliers: functions whose duration was greater than
    # two standard deviations higher than the average.
    #
    dbFile.write("CREATE TABLE outliers as (WITH with_stats as "
                    "(SELECT trace.id, trace.duration, avg_stdev.avg, "
                    "avg_stdev.stdev FROM "
                    "trace INNER JOIN avg_stdev ON trace.func=avg_stdev.func "
                    "WHERE trace.dir=1 AND duration > avg + 2 * stdev) "
                    "SELECT trace.id, dir, func, tid, time, "
                    "with_stats.duration, avg, stdev FROM trace INNER JOIN "
                    "with_stats ON trace.id=with_stats.id WHERE dir = 0);\n");

    dbFile.close();

def appendAllTraceRecordsGzipped(dbFileName, intermediateFileNames):

    gzippedFile = gzip.open(dbFileName, 'ab');

    for name in intermediateFileNames:
        fname = getPrefix(name) + ".sql";
        file = open(fname, "r");
        print("Appending data from " + fname + "...");

        shutil.copyfileobj(file, gzippedFile);

    gzippedFile.close();


def appendAllTraceRecords(dbFileName, intermediateFileNames):

    for name in intermediateFileNames:
        fname = getPrefix(name) + ".sql";
        print("Appending data from " + fname + "...");
        command = "cat " + fname + " >> " + dbFileName;

        if (os.system(command)):
            print("Could not append data from file " + fname +
                  " to " + dbFileName);


def waitOnOneProcess(runningProcesses):

    success = False;
    for fname, p in runningProcesses.items():
        if (not p.is_alive()):
            del runningProcesses[fname];
            print("Process for " + color.BOLD + fname + color.END +
                  " terminated.");
            success = True;

    # If we have not found a terminated process, sleep for a while
    if (not success):
        time.sleep(5);


def createRegularDbFile(dbFileName, totalRecords, successfullyProcessedFiles):

    dbFile = open(dbFileName, "w+");
    createDBFileHead(dbFile, totalRecords);
    dbFile.close();

    appendAllTraceRecords(dbFileName, successfullyProcessedFiles);

    dbFile = open(dbFileName, "r+");
    dbFile.seek(0, 2); # Seek to the end
    createDBFileTail(dbFile);
    dbFile.close();

def createGzippedDbFile(dbFileName, totalRecords, successfullyProcessedFiles):

    fname = dbFileName + ".gz";

    dbFile = gzip.open(fname, 'wb');
    createDBFileHead(dbFile, totalRecords);
    dbFile.close();

    appendAllTraceRecordsGzipped(fname, successfullyProcessedFiles);

    dbFile = gzip.open(fname, 'ab');
    createDBFileTail(dbFile);
    dbFile.close();

def main():

    global dbFile;
    global dbFileName;
    global firstNodeName;
    global generateTextFiles;
    global graphFilePostfix;
    global graphType;
    global htmlDir;
    global htmlTemplate;
    global lastNodeName;
    global multipleAcquireWithoutRelease;
    global noMatchingAcquireOnRelease;
    global outliersFile;
    global percentThreshold;
    global separator;
    global shortenFuncName;
    global summaryCSV;
    global summaryTxt;
    global totalRecords;
    global treatLocksSpecially;
    global tryLockWarning;
    global verbose;

    if (sys.version_info[0] != 2):
       print("This script requires python version 2 to run.");
       print("You are running version " + str(sys.version_info[0]) + "." +
             str(sys.version_info[1]));
       sys.exit(-1);

    parser = argparse.ArgumentParser(description=
                                 'Process performance log files');

    parser.add_argument('files', type=str, nargs='*',
                    help='log files to process');

    parser.add_argument('-d', '--dumpdbfile', dest='dumpdbfile', type=bool,
                        default=True,
                        help='Default: True; \
                        By default we dump a file for the entire trace that \
                        can be imported in any SQL database and is compatible \
                        with TimeSquared. Set this option to false if you want \
                        to opt out of this feature and save disk space.');

    parser.add_argument('-g', '--graphtype', dest='graphtype',
                        default='enter_exit',
                        help='Default=enter_exit; \
                        Possible values: enter_exit, func_only');

    parser.add_argument('--graph-file-postfix', dest='graphFilePostfix',
                        default='png');

    parser.add_argument('--htmlDir', dest='htmlDir', type=str,
                            default='HTML');

    parser.add_argument('-j', dest='jobParallelism', type=int,
                        default='0');

    parser.add_argument('-o', '--outliersFile',
                            dest='outliersFile',
                            default=False, action='store_true',
                            help='Default: False. Generate the file with all \
                            function records whose duration was greater than \
                            two standard deviations above the average.');

    parser.add_argument('-p', '--percent-threshold', dest='percentThreshold',
                        type=float, default = 2.0,
                        help='Default=2.0 percent.\
                        When we compute the execution flow graph, we will not \
                        include any functions, whose percent execution time   \
                        is smaller that value.');

    parser.add_argument('-r', '--regenHTML', dest='regenHTML',
                            action='store_true');

    parser.add_argument('-s', '--separator', dest='separator', default=';');
    parser.add_argument('--shorten_func_name', dest='shortenFuncName',
                            type=bool, default=True);

    parser.add_argument('--summaryCSV', dest='summaryCSV',
                            type=bool, default=True,
                            help='Generate per-file summary in CSV format');

    parser.add_argument('--summaryTxt', dest='summaryTxt',
                            type=bool, default=False,
                            help='Generate per-file summary in text format');

    parser.add_argument('--treatLocksSpecially', dest='treatLocksSpecially',
                            action='store_true',
                            help='Try to guess which functions acquire and \
                            release locks, and compute statistics about \
                            time spent holding locks based on that.');

    parser.add_argument('-t', '--generateTextFiles', dest='generateTextFiles',
                            default=False, action='store_true',
                            help='Default: False. Generate per-thread text \
                            traces in addition to the single database \
                            importable file containing records for all \
                            threads.');

    parser.add_argument('--verbose', dest='verbose', action='store_true');
    parser.add_argument('-z', dest='gzipDbFile',
                        default=True, action='store_false',
                        help="Do not gzip the final trace.sql file");

    args = parser.parse_args();

    generateTextFiles = args.generateTextFiles;
    graphType = args.graphtype;
    graphFilePostfix = args.graphFilePostfix;
    htmlDir = args.htmlDir;
    percentThreshold = args.percentThreshold;
    separator = args.separator;
    shortenFuncName = args.shortenFuncName;
    summaryCSV = args.summaryCSV;
    summmaryTxt = args.summaryTxt;
    targetParallelism = args.jobParallelism;
    treatLocksSpecially = args.treatLocksSpecially;
    verbose = args.verbose;

    print("Running with the following parameters:");
    for key, value in vars(args).items():
        print ("\t" + key + ": " + str(value));

    # Create the HTML directory
    if (createHTMLDir(htmlDir) == False):
        print("Could not create HTML directory " + htmlDir);
        return;


    # Make sure that we know where to find the HTML file templates
    # before we spend all the time parsing the traces only to fail later.
    #
    htmlTemplate = findHTMLTemplate(args.htmlDir);
    if (htmlTemplate is None):
        return;

    if (args.regenHTML):
        if (len(args.files) > 0):
            print("Regenerating the top HTML file for trace files: "
                      + str(args.files));
            print(color.BOLD + "Per-file images, image maps "
                      "and HTML files must be present in the HTML directory!" +
                      color.END);

            topHTMLFile = generateTopHTML(args.files, htmlDir);
            if (topHTMLFile is not None):
                completeTopHTML(topHTMLFile);
            return;
        else:
            print("If asking to only regenerate the top HTML, please supply " +
                      "a list of trace file names you want included.");
            return;

    if (percentThreshold > 0.0):
        print(color.RED + color.BOLD +
                  "IMPORTANT: filtering all functions whose running "
                  "time took less than " + str(percentThreshold) +
                  "% of total.\n To avoid filtering or change the default "
                  "value, use --percent-threshold argument.\n Example: "
                  "--percent-threshold=0.0" + color.END);

    # Create the file for dumping info about outliers
    #
    if (args.outliersFile):
        try:
            outliersFile = open("outliers.txt", "w");
        except:
            print ("Warning: could not open outliers.txt for writing");

    runnableProcesses = {};
    returnValues = {};
    spawnedProcesses = {};
    successfullyProcessedFiles = [];
    terminatedProcesses = {};

    # Prepare processes that will parse files, one per file
    if (len(args.files) > 0):
        for fname in args.files:
            firstUnusedId = getFirstUnusedId(fname);
            recsProcessed = Value('i', 0);
            p = Process(target=subprocessParse,
                            args=(fname, recsProcessed, firstUnusedId));
            runnableProcesses[fname] = p;
            returnValues[fname] = recsProcessed;

    # Determine the target job parallelism
    if (targetParallelism == 0):
        targetParallelism = multiprocessing.cpu_count();
        if (targetParallelism == 0):
            targetParallelism = len(args.files);

    print(color.BOLD + color.BLUE + "WILL RUN " + str(targetParallelism)
          + " JOBS IN PARALLEL." + color.END);
    print(color.BOLD + color.RED + "Reduce parallelism using -j option "
          + "if the script is killed by the OS." + color.END);

    # Spawn these processes, not exceeding the desired parallelism
    while (len(runnableProcesses) > 0):
        while (len(spawnedProcesses) < targetParallelism
               and len(runnableProcesses) > 0):

            fname, p = runnableProcesses.popitem();
            p.start();
            spawnedProcesses[fname] = p;
            print("Started process for " + color.BOLD + fname + color.END);

        # Find at least one terminated process
        waitOnOneProcess(spawnedProcesses);

    # Wait for all processes to terminate
    while (len(spawnedProcesses) > 0):
        waitOnOneProcess(spawnedProcesses);

    # Gather their return values
    for fname, retval in returnValues.items():
        if (retval.value > 0):
            successfullyProcessedFiles.append(fname);
        totalRecords += retval.value;


    print("\n" + color.BOLD +
          "ALMOST DONE! Generating images and HTML files." + color.END);

    successfullyProcessedFiles = sorted(successfullyProcessedFiles);

    # Create a file for dumping the data in a database-importable format,
    # unless the user opted out.
    #
    if (args.dumpdbfile == True):
        print("Concatenating intermediate data files into one...");
        try:
            if (args.gzipDbFile):
                createGzippedDbFile(dbFileName, totalRecords,
                                    successfullyProcessedFiles);
            else:
                createRegularDbFile(dbFileName, totalRecords,
                                    successfullyProcessedFiles);
        except:
            print(color.RED + color.BOLD + "WARNING: Something went wrong");
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback);
            print(color.END);

    topHTMLFile = generateTopHTML(successfullyProcessedFiles, htmlDir);
    if (topHTMLFile is not None):
        for fname in successfullyProcessedFiles:
            prefix = getPrefix(fname);
            generateImageAndHTMLFilesFromDot(prefix, topHTMLFile);
        completeTopHTML(topHTMLFile);



if __name__ == '__main__':
    main()
