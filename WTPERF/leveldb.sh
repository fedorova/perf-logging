#!/bin/bash
BRANCH=wt-stat-counters
WT_HOME=${HOME}/Work/WiredTiger/${BRANCH}/build_posix

BENCHMARK_HOME=${HOME}/Work/WiredTiger/leveldb
DB_HOME=/tmp/leveldb

INST_LIB=${HOME}/Work/DINAMITE/LLVM/llvm-3.5.0.src/projects/dinamite/library
DINAMITE_TRACE_DIR="/tmp"

if [ -z $1 ]; then
    BENCHMARK=readseq
else
    BENCHMARK=$1
    # Use 'fillrandom' to create the database
fi

if [[ "$BENCHMARK" == fill* ]] ; then
    USE_EXISTING_DB="0"
else
    USE_EXISTING_DB="1"
fi

if [ -z $2 ]; then
    THREADS=1
else
    THREADS=$2
fi

echo "Running " ${BENCHMARK}

DINAMITE_TRACE_PREFIX=${DINAMITE_TRACE_DIR} \
		     DYLD_LIBRARY_PATH=${INST_LIB}:${WT_HOME}/.libs:${WT_HOME}/ext/compressors/snappy/.libs/ \
		     DINAMITE_EXCLUDE_TID="1" \
		     ${BENCHMARK_HOME}/db_bench_wiredtiger  --cache_size=134217728 --use_lsm=1 \
		     --use_existing_db=${USE_EXISTING_DB} --db=${DB_HOME} --benchmarks=${BENCHMARK} \
		     --threads=${THREADS} --reads=200000
cp ${WT_HOME}/map_* ./
