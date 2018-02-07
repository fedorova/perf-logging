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
#DB_HOME=$HOME/Work/WiredTiger/WT_TEST
SCRIPT_HOME=${HOME}/Work/WiredTiger/perf-logging/WTPERF
#SCRIPT_HOME=${WT_HOME}/../bench/wtperf/runners
#OUTPUT_ROOT=${HOME}/Work/WiredTiger/WTPERF/EVICTION
OUTPUT_ROOT=.
DATE=`date +%Y-%b-%d-%H:%M`
EVICT_WORKERS=DEF
INST_LIB=${HOME}/Work/DINAMITE/LLVM/llvm-3.5.0.src/projects/dinamite/library
#WORKLOAD="500m-btree-50r50u.wtperf"
#WORKLOAD="500m-btree-80r20u.wtperf"
#WORKLOAD="500m-btree-populate.wtperf"
#WORKLOAD="checkpoint-schema-race-run.wtperf"
#WORKLOAD="checkpoint-stress-schema-ops-run.wtperf"
#WORKLOAD="evict-btree.wtperf"
#WORKLOAD="evict-btree-run.wtperf"
#WORKLOAD="evict-btree-stress-multi.wtperf"
#WORKLOAD="evict-btree-stress.wtperf"
WORKLOAD="evict-btree-stress-multi-run.wtperf"
#WORKLOAD="evict-lsm-readonly.wtperf"
#WORKLOAD="many-table-stress.wtperf"
#WORKLOAD="medium-btree.wtperf"
#WORKLOAD="medium-multi-btree-log-run.wtperf"
#WORKLOAD="medium-multi-lsm-run.wtperf"
#WORKLOAD="mongodb-secondary-apply-run.wtperf"
#WORKLOAD="multi-btree-read-heavy-stress-run.wtperf"
#WORKLOAD="multi-btree-zipfian-workload.wtperf"
#WORKLOAD="small-btree-run.wtperf"

#DINAMITE_TRACE_DIR="/mnt/fast/sasha"
DINAMITE_TRACE_DIR="/dev/shm"
#DINAMITE_TRACE_DIR="/mnt/fast/sasha"
#DINAMITE_TRACE_DIR="/mnt/fast/sasha/MULTI-BTREE-READ-HEAVY-STRESS"
#DINAMITE_TRACE_DIR="/tmp"
#EXCLUDE_TID=""
NAME="dinamite"

#for t in 8 16 48 64 96;
for t in 4;
do
    EXPNAME=${BRANCH}-${WORKLOAD}-${NAME}-${EVICT_WORKERS}-EV-${DATE}
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
	if [ "$WORKLOAD" == 'evict-btree-run.wtperf' ] ; then
	    if [ "$OSTYPE" == 'darwin' ]; then
		DINAMITE_EXCLUDE_TID=${EXCLUDE_TID} DINAMITE_TRACE_PREFIX=${DINAMITE_TRACE_DIR} DYLD_LIBRARY_PATH=${INST_LIB} ${WT_HOME}/bench/wtperf/wtperf -h ${DB_HOME} -O ${SCRIPT_HOME}/${WORKLOAD} -o threads=\(\(count=${t},reads=1\)\) -o conn_config=\"cache_size=50M,statistics=\(fast,clear\),statistics_log=\(wait=5\),eviction=\(threads_max=${EVICT_WORKERS}\),eviction=\(threads_min=1\)\"
	    else
		DINAMITE_EXCLUDE_TID=${EXCLUDE_TID} DINAMITE_TRACE_PREFIX=${DINAMITE_TRACE_DIR} LD_LIBRARY_PATH=${INST_LIB} ${WT_HOME}/bench/wtperf/wtperf -h ${DB_HOME} -O ${SCRIPT_HOME}/evict-btree-run.wtperf -o threads=\(\(count=${t},reads=1\)\) -o conn_config=\"cache_size=50M,statistics=\(fast,clear\),statistics_log=\(wait=5\),eviction=\(threads_max=${EVICT_WORKERS}\),eviction=\(threads_min=1\)\"
	    fi
	else
	    pushd ${WT_HOME}/bench/wtperf
	    if [ "$OSTYPE" == 'darwin' ]; then
		DINAMITE_TRACE_PREFIX=${DINAMITE_TRACE_DIR} DYLD_LIBRARY_PATH=${INST_LIB} WIREDTIGER_OPTRACK=${HOME}/Work/WiredTiger/WTPERF ${WT_HOME}/bench/wtperf/wtperf -h ${DB_HOME} -O ${SCRIPT_HOME}/${WORKLOAD} -o conn_config=\"statistics=\(fast\),statistics_log=\(wait=1\),operation_tracking=\(enabled=true,path=.\)\"
	    else
		DINAMITE_TRACE_PREFIX=${DINAMITE_TRACE_DIR} LD_LIBRARY_PATH=${INST_LIB} ${WT_HOME}/bench/wtperf/wtperf -h ${DB_HOME} -O ${SCRIPT_HOME}/${WORKLOAD} -o conn_config=\"statistics=\(fast\),statistics_log=\(wait=1\),operation_tracking=\(enabled=true,path=.\)\"
	    fi
	    popd
	fi

	mv ${DB_HOME}/test.stat ${OUTPUT}/${i}/.
	mv ${DB_HOME}/CONFIG.wtperf ${OUTPUT}/${i}/.
	mv ${DB_HOME}/latency.* ${OUTPUT}/${i}/.
	mv ${DB_HOME}/monitor ${OUTPUT}/${i}/.
	mv ${DB_HOME}/WiredTigerStat* ${OUTPUT}/${i}/.
	mv ${DB_HOME}/optrack* ${OUTPUT}/${i}/.
    done
done

grep 'ops/sec' ${OUTPUT_ROOT}/${EXPNAME}*/*/test.stat


# operation_tracking=\(enabled=true,path=.\)
