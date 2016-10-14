#!/bin/bash

echo "Make sure map_* files generate by the DINAMITE compiler are in the ";
echo "current working directory";

if [ -z ${SCRIPTS_HOME} ]; then
    SCRIPTS_HOME=${HOME}/Work/WiredTiger/perf-logging/trace-processing
fi

for file in "$@";
do
    echo Working on file ${file}
    ${HOME}/Work/DINAMITE/bintrace-toolkit/trace_parser -p print \
	   -a ac_short -m \
	   ./ ${file} | ${SCRIPTS_HOME}/process-logs.py --prefix ${file}
done


