#!/usr/bin/python -tt

import sys
import argparse
import matplotlib.pyplot as plt
#import plotly.plotly as py
#import plotly.graph_objs as go

verbose = False;
multipleAcquireWithoutRelease = 0;
tryLockWarning = 0;
noMatchingAcquireOnRelease = 0;

#
# LogRecord contains all the fields we expect in the log record.

class LogRecord:

    def __init__(self, func, thread, time, otherInfo):
        self.func = func;
        self.thread = thread;
        self.time = long(time);
        self.otherInfo = otherInfo;

    def printLogRecord(self):
        print(self.func + " " + str(self.thread) + " " + str(self.time));

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
# PerfData class contains informtation about the function running
# times. For now it is simple.

class PerfData:

    def __init__(self, name, threadID):
        self.name = name;
        self.threadID = threadID;
        self.numCalls = 0;
        self.totalRunningTime = long(0);
        self.runningTimes = [];

    def getAverage(self):
        return (float(self.totalRunningTime) / float(self.numCalls));

    def printSelf(self):
        print("\t Num calls: " + str(self.numCalls));
        print("\t Total running time: " + '{:,}'.format(self.totalRunningTime)
              + " ns.");
        print("\t Average running time: "
              + '{:,}'.format(long(self.getAverage())) + " ns.");

    def showHistogram(self):
        plt.figure();
        plt.hist(self.runningTimes, bins=50, log=True);
        plt.title("Thread " + str(self.threadID) + ": " + self.name)
        plt.xlabel("Running time (nanoseconds)")
        plt.ylabel("Frequency")
        filename = "t" + str(self.threadID) + "." + self.name + ".png";
        plt.savefig(filename);

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

    def showHistogram(self):
        if(len(self.lockHeldTimes) < 1):
            return;

        plt.figure();
        plt.hist(self.lockHeldTimes, bins=50, log=True);
        plt.title("Lock " + self.name)
        plt.xlabel("Lock held time (nanoseconds)")
        plt.ylabel("Frequency")
        filename = "lock-" + self.name + ".png";
        plt.savefig(filename);

    def printSelf(self):
        print("\t Num acquire: " + str(self.numAcquire));
        print("\t Num trylock: " + str(self.numTryLock));
        print("\t Num release: " + str(self.numRelease));
        print("\t Average time in acquire: "
              + str(long(self.getAverageAcquire())) + " ns.");
        print("\t Average time in trylock: "
              + str(long(self.getAverageTryLock())) + " ns.");
        print("\t Average time in release: "
              + str(long(self.getAverageRelease())) + " ns.");
        print("\t Average time the lock was held: "
              + str(long(self.getAverageTimeHeld())) + " ns.");

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

#
# These functions process lock-related functions. One of its
# goals is to match lock releases to lock acquisitions and
# compute the time spent holding the lock. Another goal is to
# simply compute the amount of time spent in each lock-related
# action (acquire, release, trylock).
#
# All stats are organized by lock name and kept in the perFileLocks
# dictionary

perFileLocks = {}


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

#
# Generate a summary pie chart for the file, showing where we spend the time
#
'''
def generateSummaryPieChart(fileName, fileDataDictionary):

    labels = [];
    values = [];

    for funcName, funcData in fileDataDictionary.iteritems():
        labels.append(funcName);
        values.append(funcData.totalRunningTime);

    trace=go.Pie(labels=labels,values=values)
    data = [trace]
    layout = go.Layout(title=fileName, width=800, height=640)
    fig = go.Figure(data=data, layout=layout)

    py.image.save_as(fig, filename=fileName+".png")
'''

#
# A per-file dictionary of functions that we encounter in the log file.
# Each function will have a corresponding list of PerfData objects,
# one for each file it parses.

perFile = {}


def parse_file(fname, prefix):

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
    elif (prefix is not None):
        print "Reading from stdin";
        logFile = sys.stdin;
        fname = prefix;
        try:
            outputFile = open(prefix+".txt", "w");
            print("Output file is " + prefix + ".txt");
        except:
            print("Could not open output file with prefix " + prefix);
            return;

    perFile[fname] = {}
    perFileLocks[fname] = {}

    for line in logFile:

        words = line.split(" ");
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
            if(len(words) > 4):
                otherInfo = words[4:len(words)];
            rec = LogRecord(func, thread, time, otherInfo)
        except ValueError:
            print "Could not parse: " + line;
            continue;

        if(words[0] == "-->"):
            # Timestamp for function entrance
            # Push each entry record onto the stack.
            stack.append(rec);

            # If we are told to write the records to the output
            # file, do so.
            if(outputFile is not None):
                outputFile.write(line);

        elif(words[0] == "<--"):
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
                    thisFileDict = perFile[fname];

                    if(not thisFileDict.has_key(stackRec.func)):
                        newPDR = PerfData(stackRec.func, thread);
                        thisFileDict[stackRec.func] = newPDR;

                    pdr = thisFileDict[stackRec.func];
                    pdr.totalRunningTime = pdr.totalRunningTime + runningTime;
                    pdr.numCalls = pdr.numCalls + 1;
                    pdr.runningTimes.append(runningTime);
                    found = True

                    # If this is a lock-related function, do lock-related
                    # processing. stackRec.otherInfo variable would contain
                    # the name of the lock, since only the function enter
                    # record has this information, not the exit record.
                    if(stackRec.otherInfo is not None
                       and looks_like_lock(func)):
                        do_lock_processing(perFileLocks[fname], rec,
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

    print("\n");
    if(outputFile is not None):
        outputFile.close();


def main():

#    py.sign_in(username='fedorova_post.harvard.edu',
#                                      api_key='gbpph0oske')
    global verbose;
    global multipleAcquireWithoutRelease;
    global tryLockWarning;
    global noMatchingAcquireOnRelease;

    parser = argparse.ArgumentParser(description=
                                     'Process performance log files');
    parser.add_argument('files', type=str, nargs='*',
                        help='log files to process');

    parser.add_argument('--generate-histograms',
                        dest='histogram', action='store_true');
    parser.set_defaults(histogram=False);

    parser.add_argument('--prefix', dest='prefix', type=str);

    parser.add_argument('--verbose', dest='verbose', action='store_true');
    args = parser.parse_args();

    if(args.verbose):
        verbose = True;

    if(len(args.files) > 0):
        for fname in args.files:
            parse_file(fname, None);
    else: # We are reading from stdin
        if(args.prefix is None):
            print("I am told to read from stdin (no files are provided), "),
            print("but there is no prefix for the output file. "),
            print("Please use --prefix to provide it.");
            sys.exit();
        else:
            parse_file(None, args.prefix);

    # Let's print the data!
    for key, perFileDict in perFile.iteritems():
        print(" SUMMARY FOR FILE " + key + ":");
        print("------------------------------");

#        generateSummaryPieChart(key, perFileDict);

        for fkey, pdr in perFileDict.iteritems():
            print(fkey + ":");
            pdr.printSelf();
            if (args.histogram):
                pdr.showHistogram();

        print("------------------------------");

        lockDataDict = perFileLocks[key];

        print("\nLOCKS SUMMARY");
        for lockKey, lockData in lockDataDict.iteritems():
            print("Lock \"" + lockKey + "\":");
            lockData.printSelf();
            if (args.histogram):
                lockData.showHistogram();

        print("No matching acquire on release: " +
              str(noMatchingAcquireOnRelease));
        print("Trylock warning: " + str(tryLockWarning));
        print("Multiple acquire without release: " +
              str(multipleAcquireWithoutRelease));

        print("------------------------------");

if __name__ == '__main__':
    main()
