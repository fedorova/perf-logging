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

cachedObjects = {};
accessTime = 0;

def ERROR(msg):
	print(color.BOLD + color.RED + msg + color.END);
	sys.exit(1);

def dumpCachedObjects():
	global cachedObjects;

	for key, value in cachedObjects.items():
		print(f"Key: {key}, Value: {value}");

def wtFind_getField(field, string):

	fields = string.split("=");

	if (len(fields) < 2):
		ERROR("WT_find line has no " + field + " expected in " + string);

	return fields[1].strip();

def processWiredTigerLine(line):

	global cachedObjects;
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

		if (objID in cachedObjects):
			obj = cachedObjects[objID];
			obj.accessTime = accessTime;
			obj.numAccesses += 1;
			obj.readGen = read_gen;
		else:
			newObj = Object(objID, accessTime, objType);
			cachedObjects[objID] = newObj;

	elif ("Removed" in line):
		objID = -1;
		for f in fields:
			if ("Removed" in f): # This is the evict message
				evictMsgFields = f.split(" ");
				objID = evictMsgFields[3];
		if (objID == -1):
			ERROR("Invalid line in WiredTiger trace: " + line);
		elif (objID not in cachedObjects):
			ERROR("WiredTiger evicts uncached object: " + line);
		else:
			obj = cachedObjects[objID];
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
