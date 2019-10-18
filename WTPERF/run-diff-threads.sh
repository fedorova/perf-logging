#!/bin/bash
BRANCH=wt-dev
if [[ "$OSTYPE" == *"darwin"* ]]; then
    WT_HOME=${HOME}/Work/WiredTiger/${BRANCH}/build_posix
    DB_HOME=${HOME}/Work/WiredTiger/WT_TEST
else
    WT_HOME=${HOME}/Work/WiredTiger/${BRANCH}/build_posix
    DB_HOME=/mnt/data0/sasha/WT_TEST
fi

TAG=BAD
DB_FILES=`ls ${DB_HOME}/test*`
SCRIPT_HOME=${HOME}/Work/WiredTiger/perf-logging/WTPERF
#SCRIPT_HOME=${HOME}/Work/WiredTiger/wt-dev/bench/wtperf/runners
OUTPUT_ROOT=${HOME}/Work/WiredTiger/WTPERF/
#OUTPUT_ROOT=/mnt/data0/sasha/WTPERF
DATE=`date +%Y-%b-%d-%H:%M`
EVICT_WORKERS=DEF
INST_LIB=${HOME}/Work/DINAMITE/LLVM/llvm-3.5.0.src/projects/dinamite/library
ENABLE_OPTRACK=false
#PERF="perf stat -e 'syscalls:sys_enter_*'"
#PERF="perf record -e sched:sched_stat_sleep -e sched:sched_switch -e sched:sched_process_exit -a -g -o perf.data.raw"
#PERF="perf stat -d -o perf.data.stat"
#PERF="perf record"

#WORKLOAD="500m-btree-50r50u.wtperf"
#WORKLOAD="500m-btree-80r20u.wtperf"
#WORKLOAD="500m-btree-populate.wtperf"
#WORKLOAD="checkpoint-schema-race-run.wtperf"
#WORKLOAD="checkpoint-stress-schema-ops-run.wtperf"
#WORKLOAD="evict-btree.wtperf"
#WORKLOAD="evict-btree-run.wtperf"
#WORKLOAD="evict-btree-stress-multi.wtperf"
#WORKLOAD="evict-btree-stress.wtperf"
#WORKLOAD="evict-btree-stress-multi-run.wtperf"
#WORKLOAD="evict-lsm-readonly.wtperf"
#WORKLOAD="lsm-read.wtperf"
#WORKLOAD="lsm-read-9GB.wtperf"
#WORKLOAD="lsm-populate.wtperf"
#WORKLOAD="lsm-update.wtperf"
#WORKLOAD="many-table-stress.wtperf"
#WORKLOAD="medium-btree.wtperf"
#WORKLOAD="medium-multi-btree-log-run.wtperf"
#WORKLOAD="medium-multi-lsm-run.wtperf"
#WORKLOAD="mongodb-secondary-apply-run.wtperf"
#WORKLOAD="multi-btree-read-heavy-stress-run.wtperf"
#WORKLOAD="multi-btree-zipfian-workload.wtperf"
WORKLOAD="small-btree-run.wtperf"

#DINAMITE_TRACE_DIR="/mnt/fast/sasha"
DINAMITE_TRACE_DIR="/dev/shm"
#DINAMITE_TRACE_DIR="/mnt/fast/sasha"
#DINAMITE_TRACE_DIR="/mnt/fast/sasha/MULTI-BTREE-READ-HEAVY-STRESS"
#DINAMITE_TRACE_DIR="/tmp"
#EXCLUDE_TID=""
#NAME="dinamite"

IOSTAT_PID=""

#for t in 8 16 48 64 96;
for t in 'default';
do
    DATE=`date +%B-%d-%Y-%Ih%Mm`
    EXPNAME=${TAG}-${BRANCH}-${WORKLOAD}-${NAME}-${DATE}-${EVICT_WORKERS}-EV-optrack-${ENABLE_OPTRACK}
    EXPID=${EXPNAME}-${t}T
    OUTPUT=${OUTPUT_ROOT}/${EXPID}
    mkdir ${OUTPUT}
    echo Output directory: ${OUTPUT}
    # Grab the map files in case we are using a DINAMITE compilation
    if ${WT_HOME}/map_* 1> /dev/null 2>&1; then
        cp ${WT_HOME}/map_* ${OUTPUT}
    fi
#
    for i in `seq 1 1`;
    do
        mkdir ${OUTPUT}/${i}
        OPTRACK_DIR=${OUTPUT}/${i}
        pushd ${WT_HOME}/bench/wtperf

        #export WIREDTIGER_CONFIG="statistics=(cache_walk),statistics_log=(wait=1,sources=(\"file:\"))"
        #export WIREDTIGER_CONFIG="statistics=(fast),statistics_log=(wait=1,json=true),verbose=(evictserver)"
        export WIREDTIGER_CONFIG="statistics=(fast),statistics_log=(wait=5,json=true)"
        echo $WIREDTIGER_CONFIG

        if [[ "$OSTYPE" == *"darwin"* ]]; then
            DINAMITE_TRACE_PREFIX=${DINAMITE_TRACE_DIR} DYLD_LIBRARY_PATH=${INST_LIB} WIREDTIGER_OPTRACK=${HOME}/Work/WiredTiger/WTPERF ${WT_HOME}/bench/wtperf/wtperf -h ${DB_HOME} -O ${SCRIPT_HOME}/${WORKLOAD} -o conn_config=\"statistics=\(fast\),statistics_log=\(wait=1\),operation_tracking=\(enabled=${ENABLE_OPTRACK},path=${OPTRACK_DIR}\)\"
        else
            LC_TIME=en_US.UTF-8 iostat -k -t -x 1 > ${OUTPUT}/${i}/iostat.log &
            IOSTAT_PID=$!
            DINAMITE_TRACE_PREFIX=${DINAMITE_TRACE_DIR} LD_LIBRARY_PATH=${INST_LIB} ${PERF} ${WT_HOME}/bench/wtperf/wtperf -h ${DB_HOME} -O ${SCRIPT_HOME}/${WORKLOAD} -o conn_config=\"operation_tracking=\(enabled=${ENABLE_OPTRACK},path=${OPTRACK_DIR}\)\"
            if ls perf.data* 1> /dev/null 2>&1; then
                mv perf.data* ${OUTPUT}/${i}
            fi
        fi
        popd

        kill ${IOSTAT_PID}

        mv ${DB_HOME}/test.stat ${OUTPUT}/${i}/.
        mv ${DB_HOME}/CONFIG.wtperf ${OUTPUT}/${i}/.
        mv ${DB_HOME}/latency.* ${OUTPUT}/${i}/.
        mv ${DB_HOME}/monitor ${OUTPUT}/${i}/.
        mv ${DB_HOME}/WiredTigerStat* ${OUTPUT}/${i}/.
        if [ "${OPTRACK_DIR}" != "${OUTPUT}/${i}" ]; then
            mv ${OPTRACK_DIR}/optrack* ${OUTPUT}/${i}/.
        fi
    done
done

grep 'ops/sec' ${OUTPUT_ROOT}/${EXPNAME}*/*/test.stat


# operation_tracking=\(enabled=true,path=.\)
#eviction=\(threads_max=${EVICT_WORKERS}\),eviction=\(threads_min=1\)
