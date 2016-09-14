#!/bin/bash
BRANCH=wt-dev
if [ "$OSTYPE" == 'darwin' ]; then
    WT_HOME=${HOME}/Work/WiredTiger/${BRANCH}/build_posix
else
    WT_HOME=/tmpfs/${BRANCH}/build_posix
fi
DB_HOME=/tmpfs/WT_TEST/
SCRIPT_HOME=${HOME}/Work/WiredTiger/perf-logging/WTPERF
OUTPUT_ROOT=${HOME}/Work/WiredTiger/WTPERF/EVICTION
DATE=`date +%Y-%m-%d`
EVICT_WORKERS=6
INST_LIB=${HOME}/Work/DINAMITE/LLVM/llvm-3.5.0.src/projects/dinamite/library

#for t in 8 16 48 64 96;
for t in 4;
do
    EXPNAME=${BRANCH}-${EVICT_WORKERS}-EV-${DATE}
    EXPID=${EXPNAME}-${t}T
    OUTPUT=${OUTPUT_ROOT}/${EXPID}
    mkdir ${OUTPUT}
    # Grab the map files in case we are using a DINAMITE compilation
    cp ${WT_HOME}/map_* ${OUTPUT}
#
    for i in `seq 1 4`;
    do
	mkdir ${OUTPUT}/${i}
if [ "$OSTYPE" == 'darwin' ]; then
	DYLD_LIBRARY_PATH=${INST_LIB} ${WT_HOME}/bench/wtperf/wtperf -h ${DB_HOME} -O ${SCRIPT_HOME}/evict-btree-run.wtperf -o threads=\(\(count=${t},reads=1\)\) -o conn_config=\"cache_size=50M,statistics=\(fast,clear\),statistics_log=\(wait=10\),eviction=\(threads_max=${EVICT_WORKERS}\),eviction=\(threads_min=1\)\"
else
	LD_LIBRARY_PATH=${INST_LIB} ${WT_HOME}/bench/wtperf/wtperf -h ${DB_HOME} -O ${SCRIPT_HOME}/evict-btree-run.wtperf -o threads=\(\(count=${t},reads=1\)\) -o conn_config=\"cache_size=50M,statistics=\(fast,clear\),statistics_log=\(wait=10\),eviction=\(threads_max=${EVICT_WORKERS}\),eviction=\(threads_min=${EVICT_WORKERS}\)\"
fi
#
	mv ${DB_HOME}/test.stat ${OUTPUT}/${i}/.
	mv ${DB_HOME}/CONFIG.wtperf ${OUTPUT}/${i}/.
	mv ${DB_HOME}/WiredTigerStat* ${OUTPUT}/${i}/.
	python ${WT_HOME}/../tools/wtstats/wtstats.py --clear ${OUTPUT}/${i}/WiredTigerStat*
	mv wtstats.html ${OUTPUT}/${i}/.
    done
done

grep 'read oper' ${OUTPUT_ROOT}/${EXPNAME}*/*/test.stat
grep 'read oper' ${OUTPUT_ROOT}/${EXPNAME}*/*/test.stat | awk '{print $6}'







