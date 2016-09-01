#!/bin/bash

BRANCH=wt-dev-din
if [ "$OSTYPE" == 'darwin' ]; then
    BUILD_DIR=${HOME}/Work/WiredTiger/${BRANCH}/build_posix
else
    BUILD_DIR=/tmpfs/${BRANCH}/build_posix
fi

if [ -z ${SCRIPTS_HOME} ]; then
    SCRIPTS_HOME=${HOME}/Work/WiredTiger/perf-logging/trace-processing
fi

for file in "$@";
do
    echo Working on file ${file}
    ${HOME}/Work/DINAMITE/bintrace-toolkit/trace_parser -p print -m ${BUILD_DIR} ${file} > ${file}.txt
    ${SCRIPTS_HOME}/process-logs.py ${file}.txt > ${file}.summary.txt
#    ${SCRIPTS_HOME}/timing_to_synoptic.py ${file}.txt
#    ${SCRIPTS_HOME}/run-synoptic.sh ${file}.txt.synoptic
done
