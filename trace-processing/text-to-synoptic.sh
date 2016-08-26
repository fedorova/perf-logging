#!/bin/sh

if [ -z ${SCRIPTS_HOME} ]; then
    SCRIPTS_HOME=${HOME}/Work/WiredTiger/perf-logging/trace-processing
fi

for file in "$@";
do
    ${SCRIPTS_HOME}/timing_to_synoptic.py $file
    ${SCRIPTS_HOME}/run-synoptic.sh ${file}.synoptic
done
