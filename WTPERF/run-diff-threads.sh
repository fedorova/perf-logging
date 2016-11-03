#!/bin/bash
BRANCH=wt-dev
if [ "$OSTYPE" == 'darwin' ]; then
    WT_HOME=${HOME}/Work/WiredTiger/${BRANCH}/build_posix
else
#    WT_HOME=/tmpfs/${BRANCH}/build_posix
    WT_HOME=${HOME}/Work/WiredTiger/${BRANCH}/build_posix
fi
#DB_HOME=/tmp/WT_TEST/
DB_HOME=/mnt/fast/sasha/WT_TEST/
SCRIPT_HOME=${HOME}/Work/WiredTiger/perf-logging/WTPERF
OUTPUT_ROOT=${HOME}/Work/WiredTiger/WTPERF/EVICTION
DATE=`date +%Y-%b-%d-%H:%M`
EVICT_WORKERS=4
INST_LIB=${HOME}/Work/DINAMITE/LLVM/llvm-3.5.0.src/projects/dinamite/library
#WORKLOAD="evict-btree-stress-multi.wtperf"
#WORKLOAD="500m-btree-80r20u.wtperf"
WORKLOAD="500m-btree-50r50u.wtperf"
#WORKLOAD="500m-btree-populate.wtperf"
DINAMITE_TRACE_DIR="/tmp"

#for t in 8 16 48 64 96;
for t in 4;
do
    EXPNAME=${BRANCH}-${WORKLOAD}-${EVICT_WORKERS}-EV-${DATE}
    EXPID=${EXPNAME}-${t}T
    OUTPUT=${OUTPUT_ROOT}/${EXPID}
    mkdir ${OUTPUT}
    echo Output directory: ${OUTPUT}
    # Grab the map files in case we are using a DINAMITE compilation
    cp ${WT_HOME}/map_* ${OUTPUT}
#
    for i in `seq 1 1`;
    do
	mkdir ${OUTPUT}/${i}
	if [ "$WORKLOAD" == 'evict-btree' ]; then
	    if [ "$OSTYPE" == 'darwin' ]; then
		DINAMITE_TRACE_PREFIX=${DINAMITE_TRACE_DIR} DYLD_LIBRARY_PATH=${INST_LIB} ${WT_HOME}/bench/wtperf/wtperf -h ${DB_HOME} -O ${SCRIPT_HOME}/evict-btree-run.wtperf -o threads=\(\(count=${t},reads=1\)\) -o conn_config=\"cache_size=50M,statistics=\(fast,clear\),statistics_log=\(wait=5\),eviction=\(threads_max=${EVICT_WORKERS}\),eviction=\(threads_min=1\)\"
	    else
		DINAMITE_TRACE_PREFIX=${DINAMITE_TRACE_DIR} LD_LIBRARY_PATH=${INST_LIB} ${WT_HOME}/bench/wtperf/wtperf -h ${DB_HOME} -O ${SCRIPT_HOME}/evict-btree-run.wtperf -o threads=\(\(count=${t},reads=1\)\) -o conn_config=\"cache_size=50M,statistics=\(fast,clear\),statistics_log=\(wait=5\),eviction=\(threads_max=${EVICT_WORKERS}\),eviction=\(threads_min=1\)\"
	    fi
	elif [[ "$WORKLOAD" == evict-btree-stress* ]]; then
	    DINAMITE_TRACE_PREFIX=${DINAMITE_TRACE_DIR} DYLD_LIBRARY_PATH=${INST_LIB} ${WT_HOME}/bench/wtperf/wtperf -h ${DB_HOME} -O ${SCRIPT_HOME}/${WORKLOAD} -o conn_config=\"eviction=\(threads_max=${EVICT_WORKERS}\),eviction=\(threads_min=1\)\"
	elif [[ "$WORKLOAD" == 500m-btree* ]]; then
	    pushd ${WT_HOME}/bench/wtperf
	    ./wtperf -h ${DB_HOME} -O ${WT_HOME}/../bench/wtperf/runners/${WORKLOAD} -o conn_config=\"eviction=\(threads_max=${EVICT_WORKERS}\),eviction=\(threads_min=1\),statistics_log=\(wait=30,json=false\)\"
	    popd
	fi
#
	mv ${DB_HOME}/test.stat ${OUTPUT}/${i}/.
	mv ${DB_HOME}/CONFIG.wtperf ${OUTPUT}/${i}/.
	mv ${DB_HOME}/latency.* ${OUTPUT}/${i}/.
	mv ${DB_HOME}/monitor ${OUTPUT}/${i}/.
	mv ${DB_HOME}/WiredTigerStat* ${OUTPUT}/${i}/.
	python ${WT_HOME}/../tools/wtstats/wtstats.py --clear ${OUTPUT}/${i}/WiredTigerStat*
	mv wtstats.html ${OUTPUT}/${i}/.
    done
done

grep 'read oper' ${OUTPUT_ROOT}/${EXPNAME}*/*/test.stat
grep 'read oper' ${OUTPUT_ROOT}/${EXPNAME}*/*/test.stat | awk '{print $6}'
grep 'ops/sec' ${OUTPUT_ROOT}/${EXPNAME}*/*/test.stat







