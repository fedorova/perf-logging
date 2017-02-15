#!/bin/sh

BUILD_DIR=`pwd`

echo ${BUILD_DIR}

ALLOC_IN="${HOME}/Work/WiredTiger/perf-logging/dinamite" DIN_FILTERS="${HOME}/Work/WiredTiger/perf-logging/dinamite/function_filter.json" DIN_MAPS="${BUILD_DIR}" INST_LIB=${HOME}/Work/DINAMITE/LLVM/llvm-3.5.0.src/projects/dinamite/library make -j 24


