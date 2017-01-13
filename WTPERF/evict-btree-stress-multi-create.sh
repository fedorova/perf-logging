#!/bin/bash
BRANCH=wt-2898
if [ "$OSTYPE" == 'darwin' ]; then
    WT_HOME=${HOME}/Work/WiredTiger/${BRANCH}/build_posix
else
    WT_HOME=/tmpfs/${BRANCH}/build_posix
fi
DB_HOME=/mnt/scratch/WT_TEST
SCRIPTS_HOME=$HOME/Work/WiredTiger/perf-logging/WTPERF

mkdir ${DB_HOME}
rm ${DB_HOME}/*


${WT_HOME}/bench/wtperf/wtperf -h ${DB_HOME} -O ${SCRIPTS_HOME}/evict-btree-stress-multi-create.wtperf
