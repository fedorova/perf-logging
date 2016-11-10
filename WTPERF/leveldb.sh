#!/bin/bash
BRANCH=wt-stat-counters
WT_HOME=${HOME}/Work/WiredTiger/${BRANCH}/build_posix

BENCHMARK_HOME=${HOME}/Work/WiredTiger/leveldb
DB_HOME=/tmpfs/leveldb

INST_LIB=${HOME}/Work/DINAMITE/LLVM/llvm-3.5.0.src/projects/dinamite/library
DINAMITE_TRACE_DIR="/tmpfs"

if [ -z $1 ]; then
    BENCHMARK=read
else
    BENCHMARK=$1
fi

if [ -z $2 ]; then
    THREADS=1
else
    THREADS=$2
fi

if [ "$BENCHMARK" == 'fill' ] ; then
    echo "Will fill the database"
    DYLD_LIBRARY_PATH=${WT_HOME}/.libs:${WT_HOME}/ext/compressors/snappy/.libs/ \
		     ${BENCHMARK_HOME}/db_bench_wiredtiger --cache_size=134217728 --use_lsm=1 \
		     --threads=1 --db=${DB_HOME} --benchmarks=fillrandom
else
    echo "Will read the database"
    DINAMITE_TRACE_PREFIX=${DINAMITE_TRACE_DIR} \
	DYLD_LIBRARY_PATH=${INST_LIB}:${WT_HOME}/.libs:${WT_HOME}/ext/compressors/snappy/.libs/ \
	${BENCHMARK_HOME}/db_bench_wiredtiger  --cache_size=134217728 --use_lsm=1 \
	--use_existing_db=1 --db=${DB_HOME} --benchmarks=readseq --threads=${THREADS} \
	--reads=200000
fi
	       
cp ${WT_HOME}/map_* ./