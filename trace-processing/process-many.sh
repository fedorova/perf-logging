#!/bin/bash

if [ -z ${SCRIPTS_HOME} ]; then
    SCRIPTS_HOME=${HOME}/Work/WiredTiger/perf-logging/trace-processing
fi

for file in "$@";
do
    echo Working on file ${file}
    ${SCRIPTS_HOME}/process-logs.py ${file} > ${file}.summary
done
