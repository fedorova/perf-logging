#!/usr/local/bin/python -tt

import argparse
import gzip
import re
import subprocess
import os

# This script takes as its input thread logs which capture the execution of a
# multi-threaded system and outputs a ShiViz representation of that execution.
# For more details on ShiViz, see
# http://bestchai.bitbucket.org/shiviz/index.html.
#
# ShiViz was originally designed to vizualize communication between processes in
# a distributed system.  In the ShiViz representation of a multi-threaded
# execution, "communication" occurs when a thread releases a lock protecting a
# shared resource and another thread acquiring the same lock some time later.
#
# In general, the script exepcts that each line in a thread log will have the
# following format:
# (-->|<--) $function $thread_number $timestamp
#
# where:
# $function is a function which the thread is executing
#  --> and <-- are arrows indicating if the thread is entering or exiting
# the function respectively
# $thread_number is the number assigned to the thread
# $timestamp is the time when the thread entered or exited the function
#
# If the function is acquiring or releasing a lock, then the line in a thread
# log will have the following format:
# (-->|<--) $function $thread_number $timestamp $lockname
#
# where $lockname is the name of the lock being acquired or released by the
# thread.

# The 'directory' variable holds the directory where the thread logs are
# located.
#directory = input("Enter directory where thread logs are located: ")
directory = "."

# For each thread in the the multi-threaded system, the script generates a
# thread object.  All thread objects are placed in the threads array.
threads = {}
nthreads = 0;

# The script creates a lock object for each lock used in the multi-threaded
# system.  The lock objects are all placed in the locks array.
locks = []

variables = {};

def getVarPtr(event):
    assert(len(event) > 4);
    return event[4];

def getVarName( event ):
    assert(len(event) > 6);
    varname = event[6]
    return varname;

def getVarType( event ):
	assert(len(event) > 5)
	vartype = event[5]
	return vartype;

def getVarValue( event ):
    if (len(event) > 7):
        return event[7]
    return "Unknown";

def var_get( ptr ):

    if (ptr not in variables):
        var = SharedVariable(ptr);
        variables[ptr] = var;
    else:
        var = variables[ptr];

    return var;

# getLockName
#
# This function analyzes a line from a thread log to obtain the name of the
# lock, if any.
#
# The input is expected to be a space-delimited array, not a string.
def getLockName( event ):
	# If there is a lock name, the format of the line will be
	# (-->|<--) $function $thread_number $timestamp $lockname.
	# Therefore, a line transformed into a space-delimited array will have a
	# length of 5 or higher.  If $function did not involve acquiring or
	# releasing locks, the length would only  be 4.
	assert(len(event) > 4)

	# Create the string lockname.
	lockname = "_".join(event[4:len(event)])

	# Return lockname as the name of the lock.
	return lockname



# lock_get
#
# This function iterates through the locks array and returns the lock object
# containing the name 'lockname'.
def lock_get( lockname ):
	for i in range(0, len(locks)):

		# Iterate through the locks array.  Return the lock object which
		# contains the name 'lockname'.
		if locks[i].name == lockname:
			return locks[i]

	# If none of the lock objects in the locks array have the name
	# 'lockname', return False.
	return False

# lock_add
#
# This function adds a new lock object to the locks array.
def lock_add( lockname ):

	# Create a new lock object with the name 'lockname'.
	lock_obj = Lock(lockname)
	# Add the lock object to the locks array
	locks.append(lock_obj)
	# Return the lock object
	return lock_obj

# isLockEvent
#
# This function analyzes a line in a thread log to determine if the line
# captures an event involving a lock.
#
# The input is expected to be a space-delimited array, not a string.
def isLockEvent( event ):
	# For this function to work properly, the input must have a length
	# greater than 1.
	assert(len(event) > 1)

	# Obtain the function being executed.
	function = event[1]
	# Determine if the function interacts with a lock.
	isLock = re.search(r'lock', function)

	# Return True if the function interacts with a lock.  Otherwise, return
	# False.
	if isLock:
		return True

	else:
		return False

def isMemoryAccess(event):
    if (event[0] == "@"):
        return True;
    else:
        return False;

def isReadingVar( event ):
	assert(len(event) > 1)

	if event[0] == "@" and event[1] == "r":
		return True
	else:
		return False

def isWritingVar( event ):
	assert(len(event) > 1)

	if event[0] == "@" and event[1] == "w":
		return True
	else:
		return False

# isEnteringLock
#
# This function analyzes a line in a thread log to determine if the thread
# entered into a function acquiring a lock.
#
# The input is expected to be a space-delimited array, not a string.
def isEnteringLock( event ):
	#For this function to work properly, the input must have a length
	# greater than 1.
	assert(len(event) > 1)

	direction = event[0]
	# Determine if the thread was entering a function.
	isEntering = re.match(r'-->', direction)
	if isEntering:
		# If the thread was entering a function, determine if that
		# function involved acquiring a lock.

		function = event[1]

		isUnlocking = re.search(r'unlock', function)
		if isUnlocking:
			# If the function was releasing a lock, return
			# False.
			return False

		isLock = re.search(r'lock', function)
		if isLock:
			# If the function was acquiring a lock, return True.
			return True
		else:
			# Otherwise, return False.
			return False
	else:
		# If the thread was exiting a function, return False.
		return False

# isExitingLock
#
# This function analyzes a line in a thread log to determine if the thread
# exited a function acquiring a lock.
#
# The input is expected to be a space-delimited array, not a string.
def isExitingLock( event ):
	# For this function to work properly, the input must have a length
	# greater than 1.
	assert(len(event) > 1)

	direction = event[0]
	# Determine if the thread is exiting a function.
	isExiting = re.match(r'<--', direction)
	if isExiting:
		# If te thread is exiting a function, determine if that function
		# involved acquiring a lock.

		function = event[1]

		isUnlocking = re.search(r'unlock', function)
		if isUnlocking:
			# If the function was releasing a lock, return False.
			return False

		isLock = re.search(r'lock', function)
		if isLock:
			# If the function was acquiring a lock, return True.
			return True
		else:
			# Otherwise, return False.
			return False
	else:
		# If the thread was entering a function, return False.
		return False

# isTryLockEvent
#
# This function analyzes a line from a thread log to determine if the thread was
# executing a 'trylock' function.
#
# The input is expected to be a space-delimited array, not a string.
def isTryLockEvent( event ):
	# For this function to work properly, the length of the input must be
	# greater than 1.
	assert(len(event) > 1)

	# Obtain the function that the thread was executing.
	function = event[1]

	# Determine if the function was a 'trylock' function.
	isTryLock = re.search(r'trylock', function)
	if isTryLock:
		# If the function was a 'trylock' function, return True.
		return True
	else:
		# Otherwise, return False.
		return False

# isYielding
#
# This function analyzes a line from a thread log to determine if the thread was
# yielding.  The thread which "tries" acquiring a lock but fails will yield to
# the other threads.
#
# The input is expected to be a space-delimited array, not a string.
def isYielding( event ):
	# For this function to work properly, the length of the input must be
	# greater than 1.
	assert(len(event) > 1)

	if event[0] == "@":
		return False

	direction = event[0]
	# Determine if the thread was entering a function.
	isEntering = re.match(r'-->', direction)
	if isEntering:
		# If the thread was entering a function, determine if that
		# function was a yield.
		function = event[1]

		isYield = re.search(r'yield', function)
		if isYield:
			# If the function was a yield, return True.
			return True
		else:
			# Otherwise, return False.
			return False
	else:
		# If the thread was exiting a function, return False.
		return False

# isUnlocking
#
# This function analyzes a line from a thread log to determine if the thread was
# entering into a function releasing a lock.
#
# The input is expected to be a space-delimited event, not a string.
def isUnlocking( event ):
	# For this function to work properly, the length of the input must be
	# greater than 1.
	assert(len(event) > 1)

	direction = event[0]
	# Determine if the thread was entering into a function.
	isEntering = re.match(r'-->', direction)
	if isEntering:
		# If the thread was entering a function, determine if that
		# function was releasing a lock.
		function = event[1]

		isUnlock = re.search(r'unlock', function)
		isRelease = re.search(r'release', function)

		if isUnlock:
			# If the function was unlocking a lock, return True.
			return True

		elif isRelease:
			# If the function was releasing a lock, return True.
			return True

		else:
			# Otherwise, return False.
			return False
	else:
		# If the thread was exiting a function, return False.
		return False

# getEventName
#
# This function forms an event name from a line in a thread log.
#
# The input is expected to be a space-delimited array, not a string.
def getEventName( event ):
	# For this function to work properly, the input must have a length
	# of 4 or greater.
    assert(len(event) >= 4)

    direction = event[0]
	# Determine if the thread was entering a function.

    if direction == "-->":
        direction = "Entering"

    elif direction == "<--":
        direction = "Exiting"

    elif direction == "@" and event[1] == "r":
        direction = "Read"
        prop = " from "

    elif direction == "@" and event[1] == "w":
        direction = "Write"
        prop = " to "
    else:
        print "Invalid event in getEventName():";
        print direction;
        print event;

    if isLockEvent(event):

		# If the thread was interacting with a lock, the event name is
		# the direction, lockname, and function combined into a string.
        event_name  = direction + " " +  getLockName(event) + "_" + event[1]

    elif isMemoryAccess(event):
        event_name = direction + " " + getVarValue(event) + prop \
          + getVarName(event) + " of type " + getVarType(event)  \
          + " (ptr=" + format(int(getVarPtr(event), 16), '02x') + ")";

    else:
        # Otherwise, the event name is the direction and function
        # combined into a string.
        event_name = direction + " " + event[1]

	# Return the event name.
    return event_name

# create_vc_header
#
# This function creates a vc header from a line in a thread log.
#
# Each entry in the ShiViz-compatible log generated by this script consists of
# two parts: the "vc header" and the "formatted vector clock".  The vc header
# contains the timestamp and event name.
#
# The input is expected to be a space-delimited array, not a string.
def create_vc_header(event):
	# For this function to work properly, the input must have a length of 4
	# or greater.
	assert(len(event) >= 4)

	# Obtain the timestamp.
	timestamp = event[3]
	# Obtain the event name.
	event_name = getEventName(event)
	# Create the vc header.
	vc_header =  timestamp + " " + event_name

	# Return the vc header.
	return vc_header

# format_vectorclock
#
# This function creates a (JSON) formatted vector clock.  The formatted vector
# clock forms a part of each entry in the ShiViz-compatible log generated by
# this script.
#
# This function has two inputs: host and vectorclock.  The host refers to the
# thread executing the event and vectorclock is the thread's vector clock.
def format_vectorclock(host, vectorclock):
	# Check that the length of vectorclock is equal to nthreads.
	assert(len(vectorclock) == nthreads+2)
	vc_entries = []

	# Create the JSON formatted vector clock.
	for i in range(0, len(vectorclock)):
		if vectorclock[i] > 0:
			vc_entry = "\"thread" + str(i) + "\":" + str(vectorclock[i])
			vc_entries.append(vc_entry)

	formatted_vc = ", ".join(vc_entries)
	formatted_vc = host + " {" + formatted_vc + "}"

	# Return the formatted vector clock.
	return formatted_vc

# vc_max
#
# This function compares the elements in two vector clocks and returns a new
# vector clock containing the maximum of those elements.
def vc_max(vc1, vc2):
	# Check that the two input vector clocks have the same length.
	assert(len(vc1) == len(vc2))
	# Check that the length of the vector clocks is nthreads.
	assert(len(vc1) == nthreads+2)

	ret = len(vc1)*[0]

	for i in range(0, len(vc1)):
		# Iterate through the input vector clocks.  Set the element of
		# the new vector clock to be the maximum of the elements in both
		# input vector clocks.
		ret[i] = max(vc1[i], vc2[i])

	# Return the new vector clock.
	return ret

class Thread:

    def __init__(self, t_id, file):
        # isTryingLock is a flag indicating if the thread is trying to
        # acquiring a lock.
        self.isTryingLock = False;

        # buffered_event is only used if a thread is trying to acquire a
        # lock.
        self.buffered_event= [0];

        # vc tracks the thread's most recent vector clock.
        self.vc = (nthreads+2)*[0];

        # t_id holds the thread number.  The thread number can be found
        # in each line of the thread log.
        self.t_id = t_id;

        # The output file of vector clock events for this thread.
        self.outfile = file;

	# The class method "executed_localevent" is invoked if the thread
	# executed a local event (aka any event which does not involve
	# communication between two threads).
	#
	# The input to this method is a line from a thread log transformed into
	# a self-delimited array.
    #
    def executed_localevent(self, event):
		# For this method to work properly, the input must have a length
		# of 4 or greater.
        assert(len(event) >= 4)

		# Increment the thread's local clock.
        self.vc[self.t_id]+=1
        host = "thread" + str(self.t_id)

		# Obtain the vc header.
        vc_header = create_vc_header(event)

		# Obtain the (JSON) formatted vector clock.
        formatted_vc = format_vectorclock(host, self.vc)

		# Write the vc header and the formatted vector clock to the
		# thread's output log.
        self.outfile.write(vc_header)
        self.outfile.write("\n")
        self.outfile.write(formatted_vc)
        self.outfile.write("\n")

    def read_var(self, event):

        varPtr = getVarPtr(event);
        var_obj = var_get(varPtr)

        local_clk = self.vc[self.t_id] + 1

        self.vc = vc_max(self.vc, var_obj.vc_lastwriter)
        self.vc[self.t_id] = local_clk

        host = "thread" + str(self.t_id)

        # Obtain the vc header.
        vc_header = create_vc_header(event)

        # Obtain the (JSON) formatted vector clock.
        formatted_vc = format_vectorclock(host, self.vc)

		# Write the vc header and the formatted vector clock to the
		# thread's output log.
        self.outfile.write(vc_header)
        self.outfile.write("\n")
        self.outfile.write(formatted_vc)
        self.outfile.write("\n")

    def write_var(self, event):

        varPtr = getVarPtr(event)
        var_obj = var_get(varPtr)

        self.vc[self.t_id]+=1

        host = "thread" + str(self.t_id)

		# Obtain the vc header.
        vc_header = create_vc_header(event)

		# Obtain the (JSON) formatted vector clock.
        formatted_vc = format_vectorclock(host, self.vc)

		# Write the vc header and the formatted vector clock to the
		# thread's output log.
        self.outfile.write(vc_header)
        self.outfile.write("\n")
        self.outfile.write(formatted_vc)
        self.outfile.write("\n")

        var_obj.vc_lastwriter = list(self.vc)

	# The class method "acquired_lock" is invoked when a thread acquired a
	# lock.
	#
	# The input to this method is a line from a thread log transformed into
	# a space-delimited array.
    def acquired_lock(self, event):
		# For this method to work properly, the input must have a length
		# of 5 or greater.
        assert(len(event) >= 5)

		# Obtain the name of the lock
        lockname = getLockName(event)
		# Retrieve from the locks array the lock object containing the
		# lock name.
        lock_obj = lock_get(lockname)

        if lock_obj == False:
            print("Could not find lock %s" %lockname)
			# If none of the lock objects in the locks array has the
			# name "lockname", create a new lock object and add it
			# to the locks array.
            lock_obj = lock_add(lockname)

		# Increment the thread's local clock.
        local_clk = self.vc[self.t_id] + 1

		# A "communication" occurs between a thread which released a
		# lock and another thread acquiring the same lock.  Therefore,
		# the thread's new vector clock is a maximum of the thread's
		# vector clock and the vector clock of the thread which
		# previously owned the lock.
        self.vc = vc_max(self.vc, lock_obj.vc_lastowner)

		# The thread's local clock is set to local_clk.
        self.vc[self.t_id] = local_clk

        host = "thread" + str(self.t_id)

		# Obtain the vc header.
        vc_header = create_vc_header(event)

		# Obtain the (JSON) formatted vector clock.
        formatted_vc = format_vectorclock(host, self.vc)

		# Write the vc header and the formatted vector clock to the
		# thread's output log.
        self.outfile.write(vc_header)
        self.outfile.write("\n")
        self.outfile.write(formatted_vc)
        self.outfile.write("\n")

	# The method "tryinglock" is invoked if the thread was trying to acquire
	# a lock (aka exiting a trylock function).  The input to this method is
	# a line from the thread log transformed into a space-delimited array.
	#
	# Typically, a thread entering a lock function will only exit that lock
	# function if it has successfully acquired the lock.  However, if the
	# thread enters a trylock function, it can exit the trylock function
	# without successfully acquiring the lock.
	#
	# When the script calls the "tryinglock" method, it does not yet know if
	# the thread has acquired the lock.  In other words, the script does not
	# yet know if the thread executed a local event (failed to acquire the
	# lock) or if the thread communicated with another thread (acquired the
	# lock).  So the "tryinglock" method temporarily buffers the input
	# "event" and sets the isTryingLock flag to True.
    def tryinglock(self, event):
        assert(len(event) >= 5)

        self.buffered_event = event
        self.isTryingLock = True


	# The method "failed_trylock" is invoked when the script determines that
	# a thread exited a trylock function without acquiring the lock.  A thread
	# which exits a trylock function without acquiring the lock will yield
	# to other threads.
	#
	# If the thread exits a trylock function without acquiring the
	# lock, then exiting a trylock function is a local event executed by the
	# thread.  The event of exiting a trylock function is buffered in
	# self.buffered_event by the tryingLock method.
	#
	# The input to the failed_trylock" method is the line in the thread log
	# transformed into a space-delimited array.  The input should be the
	# yield event which occured right after the thread exited the trylock
	# function.
    def failed_trylock(self, event):
		# Check that the length of the input is 5 or greater.
        assert(len(event) >= 5)
		# Check that the thread was previously trying to acquire a lock
		# (aka exiting a trylock function).
        assert(self.isTryingLock == True)
		# Check that the length of the buffered event is 5 or greater.
        assert(len(self.buffered_event) >= 5)

		# Set the isTryingLock flag to False.
        self.isTryingLock = False

		# Because the thread failed to acquire the lock, exiting a
		# trylock function is a local event.  Therefore, the script only
		# needs to increment the thread's local clock.
        self.vc[self.t_id]+=1

        host = "thread" + str(self.t_id)

		# Create a vc header from the buffered event.  The buffered
		# event is the one which shows that the thread was exiting a
		# trylock function.
        vc_header = create_vc_header(self.buffered_event)

		# Create the (JSON) formatted vector clock.
        formatted_vc = format_vectorclock(host, self.vc)

		# Write the vc header and the formatted vector clock to the
		# thread's output log.
        self.outfile.write(vc_header)
        self.outfile.write("\n")
        self.outfile.write(formatted_vc)
        self.outfile.write("\n")

		# After the thread exited the trylock function, it yielded to
		# other threads.  The yield is a local event so only the
		# thread's local clock is incremented.
        self.vc[self.t_id]+=1

		# Create a vc header from event.
        vc_header = create_vc_header(event)

		# Create the (JSON) formatted vector clock.
        formatted_vc = format_vectorclock(host, self.vc)

		# Write the vc header and the formatted vector clock to the
		# thread's output log.
        self.outfile.write(vc_header)
        self.outfile.write("\n")
        self.outfile.write(formatted_vc)
        self.outfile.write("\n")

	# The class method "acquired_trylock" is invoked when the script
	# determines that the thread exited a trylock function and succesfully
	# acquired the lock.  The event of exiting a trylock function was
	# buffered in self.buffered_event by the tryingLock method.
    def acquired_trylock(self):
		# Check that the length of the buffered event is 5 or greater.
        assert(len(self.buffered_event) >= 5)
		# Check that the thread was trying to acquire a lock.
        assert(self.isTryingLock == True)

		# Set the isTryingLock flag to False.
        self.isTryingLock = False

		# Get the lock name from the buffered event.
        lockname = getLockName(self.buffered_event)
		# Obtain from the locks array the lock object containing the
		# name "lockname".
        lock_obj = lock_get(lockname)

        if lock_obj == False:
            print("Could not find lock %s" %lockname)
			# If none of the lock objects in the locks array have
			# the name "lockname", then add a new lock object to the
			# locks array.
            lock_obj = lock_add(lockname)

		# The thread successfully acquired the lock so it "communicated"
		# with the thread which previously held the lock.
        local_clk = self.vc[self.t_id] + 1
        self.vc = vc_max(self.vc, lock_obj.vc_lastowner)
        self.vc[self.t_id] = local_clk

        host = "thread" + str(self.t_id)

		# Create a vc header from the buffered event.
        vc_header = create_vc_header(self.buffered_event)

		# Create the (JSON) formatted vector clock
        formatted_vc = format_vectorclock(host, self.vc)

		# Write the vc header and formatted vector clock to the thread's
		# output log.
        self.outfile.write(vc_header)
        self.outfile.write("\n")
        self.outfile.write(formatted_vc)
        self.outfile.write("\n")

	# The class method "releasing_lock" is invoked when the thread was
	# entering into a function releasing a lock.  The input to this method
	# is a line from a thread log transformed into a space-delimited array.
    def releasing_lock(self, event):
		# Check that the length of the input is 5 or greater.
        assert(len(event) >= 5)

		# Obtain the lock name
        lockname = getLockName(event)
		# Retrieve from the locks array to the lock object containining
		# the name "lockname".
        lock_obj = lock_get(lockname)

        if lock_obj == False:
            print("Could not find lock %s" %lockname)
			# If none of the lock objects in the locks array contain
			# the name "lockname", then add a new lock object to the
			# locks array.
            lock_obj = lock_add(lockname)

		# Releasing the lock is a local event.  So the thread's vector
		# clock is updated by incrementing the local clock.
        self.vc[self.t_id]+=1

        host = "thread" + str(self.t_id)

		# Create the vc header.
        vc_header = create_vc_header(event)

		# Create the (JSON) formatted vector clock.
        formatted_vc = format_vectorclock(host, self.vc)

		# Write the vc header and the formatted vector clock to the
		# thread's output file.
        self.outfile.write(vc_header)
        self.outfile.write("\n")
        self.outfile.write(formatted_vc)
        self.outfile.write("\n")

		# Each lock object has a "vc_lastowner" field containing the
		# vector clock of the thread which previously owned the lock.
		# This field needs to be updated.
        lock_obj.vc_lastowner = list(self.vc)

class Lock:
	def __init__(self, lockname):
		self.name = lockname
		self.vc_lastowner = nthreads*[0]

class SharedVariable:
	def __init__(self, varPtr):
		self.name = varPtr
		self.vc_lastwriter = (nthreads+2)*[0]

def generate_vector_timestamps(eventsForAllThreads, outputFile, start, num):

    curRecordIdx = 0;
    started = False;

    # First, let's sort the list by timestamp
    print("Sorting events list...");
    eventsForAllThreads.sort(key=lambda ts: long(ts.split()[3]));

    # The first line in vec_clk.txt needs to be a regular expression which
    # ShiViz uses to parse through the representation.
    print("Generating vector timestamps...");

    reg_expr = "(?<timestamp>(\\d*)) (?<event>.*)\\n(?<host>\\w*) (?<clock>.*)"
    outputFile.write(reg_expr)
    outputFile.write("\n\n")

    # Process events, generate vector timestamps, write into the
    # output file
    #
    for traceRecord in eventsForAllThreads:

        # Check for starting and stopping conditions if we are
        # not parsing the entire trace.
        #
        curRecordIdx = curRecordIdx + 1;
        if (curRecordIdx - 1 < start):
            continue;
        if (curRecordIdx > start + num):
            print("Stopping processing at record " + str(curRecordIdx));
            break;

        # Be nice and show to the user some progress indicators.
        #
        if (not started):
            print("Beginning to process with record ID " + str(curRecordIdx));
            started = True;

        if ((curRecordIdx - start) % 10000 == 0):
            print(str(curRecordIdx - start) + " out of " + str(num) + "...");

        event = traceRecord.split(" ");
        try:
            t_index = int(event[2]);
            if (not threads.has_key(t_index)):
                threads[t_index] = Thread(t_index, outputFile);
        except:
            print("Dropping invalid record:" + line);
            continue;

        if (isMemoryAccess(event)):

            if (isReadingVar(event)):
                threads[t_index].read_var(event)
            elif (isWritingVar(event)):
                threads[t_index].write_var(event)

        elif isEnteringLock(event):
            assert(len(event) >= 4)

            # If the thread entered into a function
            # acquiring a lock, determine what lock it was
            # acquiring.
            lockname = getLockName(event)

            # Check if there is already a lock object
            # containing the lock name.  If no such lock
            # object exists, create it.
            lock_obj = lock_get(lockname)

            if lock_obj == False:
                lock_add(lockname)

            # Obtain the thread object and call the class
            # method "executed_localevent".
            threads[t_index].executed_localevent(event)

        elif isExitingLock(event):
            assert(len(event) >= 4)

            if isTryLockEvent(event):
                # If the thread exited a function which
                # was trying to acquire a lock, obtain
                # the thread object and call the class
                # method "tryinglock".
                threads[t_index].tryinglock(event)
                assert(threads[t_index].isTryingLock)

            else:
                # Otherwise, the thread definitely
                # succeeded in acquiring the lock.
                # Obtain the thread object and call the
                # class method "acquired_lock".
                threads[t_index].acquired_lock(event)

        elif threads[t_index].isTryingLock and isYielding(event):
            assert(len(event) >= 4)

            # If the thread yielded after *trying* to acquire
            # a lock, then the thread failed to obtain the
            # lock.  Retrieve the thread object and call the
            # class method "failed_trylock".
            threads[t_index].failed_trylock(event)

        elif isUnlocking(event):
            assert(len(event) >= 4)

            if threads[t_index].isTryingLock:

                # If the thread released a lock
                # immediately after *trying* to acquire
                # it, then obviously the thread had
                # succeeded in obtaining that lock.
                # Obtain the thread object and call the
                # class method "acquired_trylock".
                threads[t_index].acquired_trylock()

            # Obtain the thread object and call the class
            # method "releasing_lock".
            threads[t_index].releasing_lock(event)

        elif threads[t_index].isTryingLock:

            # If the thread did not yield after *trying* to
            # acquire a lock, then the script assumes that
            # the thread succeeded in obtaining the lock.

            # Obtain the thread object and call the class
            # method "acquired_trylock".
            threads[t_index].acquired_trylock()

            # After acquring the lock, the thread did not
            # "communicate" with other threads by releasing
            # the lock.  Therefore, the thread executed a
            # local event.  Obtain the thread object and
            # call the class method "executed_localevent".
            threads[t_index].executed_localevent(event)

        else:
            assert(len(event) >= 4)

            # The thread executed a local event.  Obtain the
            # thread object and call the class method
            # "executed_localevent".
            threads[t_index].executed_localevent(event)


eventsForAllThreads = [];
threadIDs = {};

def parse_file(fname):

    global eventsForAllThreads;
    global threadIDs;

    if(fname is not None):
        try:
            file = open(fname, "r");
            print "Parsing file " + fname;
        except:
            print "Could not open file " + fname;
            return;

    for line in file:
        words = line.split(" ");

        if (len(words) < 4):
            continue;

        if ((words[0] == "-->") or
                (words[0] == "<--") or
                    ((words[0] == "@") and
                             (words[1] == "r") or (words[1] == "w"))):

            try:
                threadID = int(words[2]);
            except:
                print("Dropping invalid record:" + line);
                continue;

            assert(threadID >= 0);
            if (not threadIDs.has_key(threadID)):
                threadIDs[threadID] = 1;

            # Looks like a valid event, add to event list.
            eventsForAllThreads.append(line.strip());
        else:
            print("Dropping invalid record:" + line);

    file.close();

def main():

    global eventsForAllThreads;
    global nthreads;

    parser = argparse.ArgumentParser(description=
                                    'Convert text traces to TSViz '
                                         'vector clock logs');
    parser.add_argument('files', type=str, nargs='*',
                            help='log files to process');
    parser.add_argument('-s', '--start', dest='starting_point',
                            default='BEGINNING');
    parser.add_argument('-n', '--numevents', dest='num_events',
                            default='ALL');

    args = parser.parse_args();

    # Create a dictionary of events in all files, keyed by the
    # timestamp
    if(len(args.files) > 0):
        for fname in args.files:
            parse_file(fname);

    print("Parsed " + str(len(eventsForAllThreads)) + " events");
    print("Identified " + str(len(threadIDs)) + " threads.");
    nthreads = len(threadIDs);

    # Let's figure out where to begin generating events and
    # how many to generate
    if (args.starting_point == 'BEGINNING'):
        start = 0;
    elif (args.starting_point == 'MIDDLE'):
        start = len(eventsForAllThreads) / 2;
    else:
        try:
            start = int(args.starting_point);
        except:
            print ("Could not convert " + args.starting_point +
                       " to an integer value for --start argument");
            return;

    if (args.num_events == "ALL"):
        num = len(eventsForAllThreads);
    else:
        try:
            num = int(args.num_events);
        except:
            print ("Could not convert " + args.num_events +
                       " to an integer value for --num_events argument");
            return;

    outputFile = open("vector_timestamps." + str(start) + "-" + str(num) +
                          ".vec", "w");
    generate_vector_timestamps(eventsForAllThreads, outputFile, start, num);
    outputFile.close()

if __name__ == '__main__':
    main()
