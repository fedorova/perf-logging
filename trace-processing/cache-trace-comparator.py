#!/usr/bin/env python3

import argparse
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

class Object:
	def __init__(self, objectId, accessTime, objType):
		self.accessTime = accessTime;
		self.cached = True;
		self.numTimesEvicted = 0;
		self.numAccesses = 0;
		self.objectId = objectId;
		self.readGen = 0;
		self.type = objType;

	def print(self):
		print(color.BOLD + f"ObjectID {self.objectId}" + color.END + "\n");
		for field, value in vars(self).items():
			print(f"\t{field}: {value}\n");

WTcachedObjects = {};
otherCachedObjects = {};
accessTime = 0;

def ERROR(msg):
	print(color.BOLD + color.RED + msg + color.END);
	sys.exit(1);

def dumpCachedObjects():
	global WTcachedObjects;

	for key, value in WTcachedObjects.items():
		value.print();

def wtFind_getField(field, string):

	fields = string.split("=");

	if (len(fields) < 2):
		ERROR("WT_find line has no " + field + " expected in " + string);

	return fields[1].strip();

def processWiredTigerLine(line):

	global WTcachedObjects;
	global accessTime;

	fields = line.split(":");

	if ("WT_find" in line):
		accessTime += 1;
		objFields = fields[5].split(",");
		objID = 0;
		objType = 0;
		read_gen = 0;

		for f in objFields:
			f = f.strip();
			if ("parent_addr" in f):
				continue;
			elif ("addr =" in f):
				objID = wtFind_getField("objID", f);
			elif ("read_gen =" in f):
				read_gen = wtFind_getField("read_gen", f);
			elif ("type =" in f):
				objType = wtFind_getField("objType", f);

		objID = int(objID);
		if (objID in WTcachedObjects):
			obj = WTcachedObjects[objID];
			obj.accessTime = int(accessTime);
			obj.numAccesses += 1;
			obj.readGen = int(read_gen);
		else:
			newObj = Object(objID, accessTime, objType);
			WTcachedObjects[objID] = newObj;

	elif ("Removed" in line):
		objID = -1;
		for f in fields:
			if ("Removed" in f): # This is the evict message
				evictMsgFields = f.split(" ");
				objID = int(evictMsgFields[3]);
		if (objID == -1):
			ERROR("Invalid line in WiredTiger trace: " + line);
		elif (objID not in WTcachedObjects):
			ERROR("WiredTiger evicts uncached object: " + line);
		else:
			obj = WTcachedObjects[objID];
			obj.cached = False;
			obj.numTimesEvicted += 1;
	else:
		ERROR("Invalid line in WiredTiger trace: " + line);

def parseWiredTigerTrace(fname):

	try:
		f = open(fname);
	except:
		ERROR("Could not open " + fname);

	for line in f.readlines():
		if ("WT_find" in line or "Removed" in line):
			processWiredTigerLine(line);

	dumpCachedObjects();

#
# Valid lines can look like this:
#
# find 2048020 3308544000
# evict 2994114560
#
# In the "find" record, the second field is virtual clock, incremented on each cache lookup.
# The third field is the object ID.
#
# In the "evict" record, the second field is the object ID.
#
def processOtherTraceLine(line):

    global otherCachedObjects;

    words = line.split(" ");

    if (words[0] == "find" and len(words) == 3):
        objID = int(words[2]);
        accessTime = int(words[1]);
        if (objID in otherCachedObjects):
            obj = otherCachedObjects[objID];
            obj.numAccesses += 1;
            obj.accessTime = accessTime;
        else:
            newObj = Object(objID, accessTime, 0);
            otherCachedObjects[objID] = newObj;
    elif(words[0] == "evict"):
        objID = int(words[1]);
        if (objID not in otherCachedObjects):
            ERROR(f"Evicted object {objID} is not in cache.\n" + line);
        else:
            obj =  otherCachedObjects[objID];
            obj.cached = False;
            obj.numTimesEvicted += 1;

def parseOtherTrace(fname):

	try:
		f = open(fname);
	except:
		ERROR("Could not open " + fname);

	for line in f.readlines():
		if ("find" in line or "evict" in line):
			processOtherTraceLine(line);

def main():

	parser = argparse.ArgumentParser(
		description= "Analyze WiredTiger cache trace in comparison with another algorithm",
		formatter_class=RawTextHelpFormatter);
	parser.add_argument('-w', '--wt', dest='wtTrace', type=str, help='WiredTiger simulator output file');
	parser.add_argument('-o', '--other', dest='otherTrace', type=str,
						help='Simulator output file for the other algorithm');

	args = parser.parse_args();

	if (args.wtTrace is None and args.otherTrace is None):
		parser.print_help();
		sys.exit(1);

	if (args.wtTrace is not None):
		parseWiredTigerTrace(args.wtTrace);
	if (args.otherTrace is not None):
		parseOtherTrace(args.otherTrace);

if __name__ == '__main__':
	main()
