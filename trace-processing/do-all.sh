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
    ${HOME}/Work/DINAMITE/bintrace-toolkit/trace_parser -p print -a ac_short -m ./ ${file} | ${SCRIPTS_HOME}/process-logs.py --prefix ${file} > ${file}.summary
    ${SCRIPTS_HOME}/timing_to_synoptic.py ${file}
    ${SCRIPTS_HOME}/run-synoptic.sh ${file}.synoptic
    ${SCRIPTS_HOME}/prettify-dotfiles.py ${file}
    dot -Tpng ${file}.synoptic-enhanced.dot > ${file}.png
done

rm *.synoptic.condensed*
