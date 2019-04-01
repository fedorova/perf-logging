#!/bin/bash
BRANCH=wt-dev
if [ "$OSTYPE" == 'darwin' ]; then
    WT_HOME=${HOME}/Work/WiredTiger/${BRANCH}/build_posix
else
    WT_HOME=${HOME}/Work/WiredTiger/${BRANCH}/build_posix
#    WT_HOME=/tmpfs/${BRANCH}/build_posix
fi
#DB_HOME=/tmp/WT_TEST
DB_HOME=/mnt/data0/sasha/WT_TEST/
#DB_HOME=$HOME/Work/WiredTiger/WT_TEST/
SCRIPTS_HOME=$HOME/Work/WiredTiger/perf-logging/WTPERF

mkdir ${DB_HOME}
rm ${DB_HOME}/*


${WT_HOME}/bench/wtperf/wtperf -h ${DB_HOME} -O ${SCRIPTS_HOME}/small-btree-create.wtperf
