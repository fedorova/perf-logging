#!/bin/bash
BRANCH=wt-dev-orig
if [[ "$OSTYPE" == *"darwin"* ]]; then
    WT_HOME=${HOME}/Work/WiredTiger/${BRANCH}/build_posix
    DB_HOME=$HOME/Work/WiredTiger/WT_TEST/
else
    WT_HOME=${HOME}/Work/WiredTiger/${BRANCH}/build_posix
    DB_HOME=/mnt/data0/sasha/WT_TEST/
fi

SCRIPTS_HOME=$HOME/Work/WiredTiger/perf-logging/WTPERF

mkdir ${DB_HOME}
rm ${DB_HOME}/*


${WT_HOME}/bench/wtperf/wtperf -h ${DB_HOME} -O ${SCRIPTS_HOME}/small-btree-create.wtperf
