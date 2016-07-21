#!/bin/sh

DIN_FILTERS="${HOME}/Work/WiredTiger/perf-logging/dinamite/function_filter.json" INST_LIB=${HOME}/Work/DINAMITE/LLVM/llvm-3.5.0.src/projects/dinamite/library make -j 4 > out 2>&1


