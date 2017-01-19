#!/usr/local/bin/python -tt

import argparse
import glob, os, re, sys
from operator import itemgetter


def readValidLine(fd):

    print("Reading line from fd " + str(fd));

    while(True):
        line = fd.readline();
        isValidLine = re.match(r'(-->|<--)\s+\w+\s+\d+\s+\d+($|\s+\w+)',
                               line);
        if (line == ""):
            # We reached the end of the file
            return None;
        elif (isValidLine):
            return line;
        else:
            # Invalid line
            print('Skipping invalid line:\n\t' + line);
            continue;

def createLineDict(line, fd):

    line = line.strip();
    line = line.split()

    direction = line[0]
    if (direction == "-->"):
        direction = "0"
    else:
        direction = "1"

    function = line[1]
    tid = line[2]
    time = line[3]

    lockname = "_".join(line[4:len(line)])
    if (lockname == ""):
        lockname = "null"

    lineDict = {'direction':direction, 'function':function, 'tid':tid,
                    'time':time, 'lockname':lockname, 'fd':fd};
    return lineDict;

def main():

    parser = argparse.ArgumentParser(description=
                                         'Process data for a database dump');
    parser.add_argument('files', type=str, nargs='*');

    args = parser.parse_args();

    fds = [];

    for file in args.files:
        # Find all trace text files.
        validFname = re.findall(r'trace.bin.\d+.txt', file);
        if (len(validFname) > 0):
            print("Found file " + file);
            try:
                fd = open(validFname[0], 'r')
                fds.append(fd);
            except:
                print("Could not open file " + validFname[0]);

    with open("preprocessed_data.txt", 'w') as fout:
        lineDicts = [];

        # Read the first line from every file.
        for fd in fds:
            line = readValidLine(fd);
            print line;

            if (line is None):
                fd.close()
                fds.remove(fd)
            else:
                lineDict = createLineDict(line, fd)
                lineDicts.append(lineDict)

        oid = 0;
        eventid = 0;
        eventids = {};

        print str(lineDicts);

        while len(lineDicts) > 0:
            lineDicts = sorted(lineDicts, key=itemgetter('time'))

            lineDict = lineDicts[0]
            direction = lineDict['direction']
            function = lineDict['function']
            tid = lineDict['tid']
            time = lineDict['time']
            lockname = lineDict['lockname']
            fd = lineDict['fd']

            if (direction == "0"):
                eventids[tid + function + lockname] = eventid
                fout.write(str(oid) + " " + str(eventid) + " " + direction
                                   + " " + function + " " + tid + " " + time
                                   + " " + lockname + "\n")
                eventid+=1
            elif (tid + function + lockname in eventids):
                fout.write(str(oid) + " "
                               + str(eventids[tid + function + lockname])
                               + " " + direction + " " + function + " "
                               + tid + " " + time + " " + lockname + "\n");
                del eventids[tid + function + lockname];
            else:
                print "Ignoring " + line;

            oid+=1
            lineDicts.remove(lineDict);

            # Read the next line from this file
            #
            line = readValidLine(fd);
            print line;
            if (line is not None):
                lineDict = createLineDict(line, fd);
                lineDicts.append(lineDict);
            else:
                fd.close()

if __name__ == '__main__':
    main()
