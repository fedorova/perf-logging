#!/usr/local/bin/python -tt

import sys
import argparse
import networkx as nx
import operator
import colorsys

graphFilePostfix = None;
graphType = None;
multipleAcquireWithoutRelease = 0;
noMatchingAcquireOnRelease = 0;
separator = " ";
tryLockWarning = 0;
verbose = False;

#
# LogRecord contains all the fields we expect in the log record.

class LogRecord:

    def __init__(self, func, op, thread, time, otherInfo):
        self.func = func;
        self.op = op;
        self.thread = thread;
        self.time = long(time);
        self.otherInfo = otherInfo;

    def printLogRecord(self):
        print(self.op + " " + self.func + " " + str(self.thread) + " "
              + str(self.time));

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

    def __init__(self, name, threadID):
        self.name = name;
        self.threadID = threadID;
        self.numCalls = 0;
        self.totalRunningTime = long(0);
        self.runningTimes = [];
        self.maxRunningTime = 0;
        self.maxRunningTimeTimestamp = 0;
        self.filtered = False;

    def getAverage(self):
        return (float(self.totalRunningTime) / float(self.numCalls));

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

    if(looks_like_acquire(funcname) or
       looks_like_release(funcname) or
       looks_like_trylock(funcname)):
        return True;
    else:
        return False;

def do_lock_processing(locksDictionary, logRec, runningTime,
                       nameWords):
    global verbose;
    global multipleAcquireWithoutRelease;
    global tryLockWarning;
    global noMatchingAcquireOnRelease;

    lockName = "";
    func = logRec.func

    # Reconstruct the lock name
    for word in nameWords:
        lockName = lockName + word.strip() + " ";
    lockName.strip();

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

#
# Figure out the percent execution time for each function relative to the total.
# Compute the colour based on the percent. Set the node colour accordingly.
# Update the node label with the percent value.
#
def augment_graph(graph, funcSummaryData, traceStats):

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
    for func, pdr in funcSummaryData.iteritems():
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

    for func, attrs in funcWithColorCode.iteritems():

        if graphType == 'func_only':
            allNames = [func];
        else:
            enterNodeName = "enter " + func;
            exitNodeName  = "exit " + func;
            allNames = [enterNodeName, exitNodeName];

        for nodeName in allNames:
            graph.node[nodeName]['label'] = nodeName + "\n" + \
                                             attrs[1];
            graph.node[nodeName]['style'] = "filled";
            graph.node[nodeName]['fillcolor'] = attrs[0];

def update_graph(graph, nodeName, prevNodeName):

    if (not graph.has_node(nodeName)):
            graph.add_node(nodeName, fontname="Helvetica");

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

    graph = nx.DiGraph();

    graph.add_node("START", fontname="Helvetica");
    graph.node["START"]['shape']='box'
    prevNodeName = "START";

    if graphType == 'func_only':
        prevNodeName = generate_func_only_graph(graph, logRecords, prevNodeName)
    else:
        for logRec in logRecords:
            nodeName = logRec.op + " " + logRec.func;
            update_graph(graph, nodeName, prevNodeName);
            prevNodeName = nodeName;

    graph.add_node("END", fontname="Helvetica");
    graph.add_edge(prevNodeName, "END");
    graph.node["END"]['shape']='diamond';

    return graph;

#
# When we compute the execution flow graph, we will not include any functions
# whose percent execution time is below that value.
#
percentThreshold = 0.0;

useMaxRuntimeFilter = False;
maxRuntimeThreshold = 3300000; # in clock cycles

def filterLogRecords(logRecords, funcSummaryRecords, traceStats):

    filteredRecords = [];
    traceRuntime = traceStats.getTotalTime();

    for rec in logRecords:

        # A log may have no corresponding function record if we stopped
        # logging before the function exit record was generated, as can
        # be with functions that start threads.
        #
        if not funcSummaryRecords.has_key(rec.func):
            print("Warning: no performance record for function " +
                  rec.func);
            continue;

        pdr = funcSummaryRecords[rec.func];
        percent = float(pdr.totalRunningTime) / float(traceRuntime) * 100;

        if (percent <= percentThreshold):
            pdr.filtered = True;
            continue;
        elif (useMaxRuntimeFilter and pdr.maxRunningTime < maxRuntimeThreshold):
            pdr.filtered = True;
            continue;
        else:
            filteredRecords.append(rec);

    return filteredRecords;

def parse_file(fname, prefix):

    startTime = 0;
    endTime = 0;
    stack = [];
    lockStack = [];
    outputFile = None;

    if(fname is not None):
        try:
            logFile = open(fname, "r");
            print "Parsing file " + fname;
        except:
            print "Could not open file " + fname;
            return;
    else:
        print "Reading from stdin";
        logFile = sys.stdin;

        try:
            outputFile = open(prefix+".txt", "w");
            print("Output file is " + prefix + ".txt");
        except:
            print("Could not open output file with prefix " + prefix);
            outputFile = sys.stdout;

    funcSummaryRecords = {}
    locksSummaryRecords = {}
    traceStats = TraceStats(prefix);
    logRecords = [];
    graph = nx.DiGraph();

    graph.add_node("START", fontname="Helvetica");
    graph.node["START"]['shape']='box'
    prevNodeName = "START";

    for line in logFile:

        words = line.split(separator);
        thread = 0;
        time = 0;
        func = "";
        otherInfo = None;

        if(len(words) < 4):
           continue;

        try:
            func = words[1];
            thread = int(words[2]);
            time = long(words[3]);
            if (len(words) > 4):
                otherInfo = words[4:len(words)];

        except ValueError:
            print "Could not parse: " + line;
            continue;

        if (words[0] == "-->"):
            op = "enter";
        elif (words[0] == "<--"):
            op = "exit";
        else:
            continue;

        rec = LogRecord(func, op, thread, time, otherInfo);
        logRecords.append(rec);

        if(startTime == 0):
            startTime = time;
        else:
            endTime = time;

        if(op == "enter"):
            # Timestamp for function entrance
            # Push each entry record onto the stack.
            stack.append(rec);

            # If we are told to write the records to the output
            # file, do so.
            if(outputFile is not None):
                outputFile.write(line);

        else:
            if(outputFile is not None):
                # If this is a function exit record, we may need to add
                # the name of the lock to the end of the line, if this
                # happens to be a lock function. So for now we write the
                # line without the newline character at the end. Later we
                # will either add the lock name with the newline character
                # (if this happens to be a lock function, or just the
                # newline character otherwise.
                outputFile.write(line.rstrip());

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

                    if(not funcSummaryRecords.has_key(stackRec.func)):
                        newPDR = PerfData(stackRec.func, thread);
                        funcSummaryRecords[stackRec.func] = newPDR;

                    pdr = funcSummaryRecords[stackRec.func];
                    pdr.totalRunningTime = pdr.totalRunningTime + runningTime;
                    pdr.numCalls = pdr.numCalls + 1;
                    pdr.runningTimes.append(runningTime);
                    if (runningTime > pdr.maxRunningTime):
                        pdr.maxRunningTime = runningTime;
                        pdr.maxRunningTimeTimeStamp = stackRec.time;
                    found = True

                    # If this is a lock-related function, do lock-related
                    # processing. stackRec.otherInfo variable would contain
                    # the name of the lock, since only the function enter
                    # record has this information, not the exit record.
                    if(stackRec.otherInfo is not None
                       and looks_like_lock(func)):
                        do_lock_processing(locksSummaryRecords, rec,
                                           runningTime,
                                           stackRec.otherInfo);
                        if(outputFile is not None):
                            for lockNamePart in stackRec.otherInfo:
                                outputFile.write(" " + lockNamePart.strip());
                    break;
            if(not found):
                print("Could not find matching function entrance for line: \n"
                      + line);

            if(outputFile is not None):
                outputFile.write("\n");

    traceStats.setStartTime(startTime);
    traceStats.setEndTime(endTime);

    # Filter the log records according to criteria on their attributes
    filteredLogRecords = filterLogRecords(logRecords, funcSummaryRecords,
                                          traceStats);

    # Augment graph attributes to reflect performance characteristics
    graph = generate_graph(filteredLogRecords);
    augment_graph(graph, funcSummaryRecords, traceStats);

    # Print the graph
    aGraph = nx.drawing.nx_agraph.to_agraph(graph);
    aGraph.add_subgraph("START", rank = "source");
    aGraph.add_subgraph("END", rank = "sink");
    graphFileName = prefix + "." + graphType + "."  \
                    + str(percentThreshold) + "%." + graphFilePostfix;

    aGraph.draw(graphFileName, prog = 'dot');
    print("Graph is saved to: " + graphFileName);

    if(outputFile is not None):
        outputFile.close();

    # Write the summary to the output file.
    try:
        summaryFileName = prefix + ".summary";
        summaryFile = open(summaryFileName, "w");
        print("Summary file is " + summaryFileName);
    except:
        print("Could not create summary file " + summaryFileName);
        summaryFile = sys.stdout;

    summaryFile.write(" SUMMARY FOR FILE " + prefix + ":\n");
    summaryFile.write("------------------------------\n");

    summaryFile.write("Total trace time: "
                      + str(traceStats.getTotalTime()) + "\n");
    summaryFile.write(
        "Function \t Num calls \t Runtime (tot) \t Runtime (avg)\n");

    for fkey, pdr in funcSummaryRecords.iteritems():
        pdr.printSelf(summaryFile);

        summaryFile.write("------------------------------\n");

    lockDataDict = locksSummaryRecords;

    summaryFile.write("\nLOCKS SUMMARY\n");
    for lockKey, lockData in lockDataDict.iteritems():
        lockData.printSelf(summaryFile);

    summaryFile.write("------------------------------\n");
    summaryFile.close();


def getPrefix(fname):

    words = fname.split(".txt");
    if (len(words) > 0):
        return words[0];
    else:
        return fname;

def main():

    global firstNodeName;
    global graphFilePostfix;
    global graphType;
    global lastNodeName;
    global multipleAcquireWithoutRelease;
    global noMatchingAcquireOnRelease;
    global percentThreshold;
    global separator;
    global tryLockWarning;
    global verbose;

    parser = argparse.ArgumentParser(description=
                                 'Process performance log files');
    parser.add_argument('files', type=str, nargs='*',
                    help='log files to process');

    parser.add_argument('--prefix', dest='prefix', type=str);

    parser.add_argument('--verbose', dest='verbose', action='store_true');

    parser.add_argument('-g', '--graphtype', dest='graphtype',
                        default='enter_exit',
                        help='Default=enter_exit; \
                        Possible values: enter_exit, func_only');

    parser.add_argument('-p', '--percent-threshold', dest='percentThreshold',
                        type=float, default = 0.0,
                        help='Default=0.0; \
                        When we compute the execution flow graph, we will not \
                        include any functions, whose percent execution time   \
                        is smaller that value.')

    parser.add_argument('--graph-file-postfix', dest='graphFilePostfix',
                        default='png');
    parser.add_argument('-s', '--separator', dest='separator', default=' ');

    args = parser.parse_args();

    if(args.verbose):
        verbose = True;

    graphType = args.graphtype;
    graphFilePostfix = args.graphFilePostfix;
    percentThreshold = args.percentThreshold;
    separator = args.separator;

    if(len(args.files) > 0):
        for fname in args.files:
            # Figure out the prefix for the output files
            if (args.prefix is None):
                prefix = getPrefix(fname);
            else:
                prefix = args.prefix;
            print("Prefix is " + prefix);
            parse_file(fname, prefix);
    else: # We are reading from stdin
        if(args.prefix is None):
            print("I am told to read from stdin (no files are provided), "),
            print("but there is no prefix for the output file. "),
            print("Please use --prefix to provide it.");
            sys.exit();
        else:
            parse_file(None, args.prefix);


if __name__ == '__main__':
    main()
