#!/bin/bash
BRANCH=wt-3190
if [ "$OSTYPE" == 'darwin' ]; then
    WT_HOME=${HOME}/Work/WiredTiger/${BRANCH}/build_posix
else
    WT_HOME=${HOME}/Work/WiredTiger/${BRANCH}/build_posix
#    WT_HOME=/tmpfs/${BRANCH}/build_posix
fi
#DB_HOME=/tmp/WT_TEST
DB_HOME=/mnt/fast/sasha/WT_TEST/
SCRIPTS_HOME=$HOME/Work/WiredTiger/perf-logging/WTPERF

mkdir ${DB_HOME}
rm ${DB_HOME}/*


${WT_HOME}/bench/wtperf/wtperf -h ${DB_HOME} -O ${SCRIPTS_HOME}/medium-multi-lsm-create.wtperf
