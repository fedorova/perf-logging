#!/bin/sh

if [ -z ${SCRIPTS_HOME} ]; then
    SCRIPTS_HOME=${HOME}/Work/WiredTiger/perf-logging/trace-processing
fi

for file in "$@";
do
    echo Working on file ${file}
    ${HOME}/Work/DINAMITE/bintrace-toolkit/trace_parser -p print -m ./ ${file} > ${file}.txt
    ${SCRIPTS_HOME}/process-logs.py ${file}.txt > ${file}.summary.txt
    ${SCRIPTS_HOME}/timing_to_synoptic.py ${file}.txt
    ${SCRIPTS_HOME}/run-synoptic.sh ${file}.txt.synoptic
done
