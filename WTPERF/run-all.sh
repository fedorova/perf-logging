#!/bin/bash

EXP_TAG="COMPR-RATIO"
POSTFIX=".new"

#export WIREDTIGER_CONFIG="mmap_all=true"
#export WIREDTIGER_CONFIG="statistics=(all)"
export WIREDTIGER_CONFIG="statistics=(all),statistics_log=(sources=(\"file:\"))"

#500m-btree-populate.wtperf

#checkpoint-latency-0.wtperf
#checkpoint-latency-1.wtperf
#evict-btree-readonly.wtperf
#evict-btree-scan.wtperf
#evict-lsm-readonly.wtperf
#many-table-stress.wtperf
#medium-lsm-async.wtperf
#metadata-split-test.wtperf

# These don't produce any interesting numbers
#mongodb-large-oplog.wtperf
#mongodb-oplog.wtperf
#mongodb-secondary-apply.wtperf
#mongodb-small-oplog.wtperf

# These store output in multiple directories
#multi-btree-long.wtperf
#multi-btree-read-heavy-stress.wtperf
#multi-btree-stress.wtperf
#multi-btree.wtperf
#multi-btree-zipfian-populate.wtperf
#multi-btree-zipfian-workload.wtperf

#parallel-pop-btree.wtperf
#parallel-pop-lsm.wtperf
#parallel-pop-stress.wtperf

#truncate-btree-populate.wtperf
#truncate-btree-workload.wtperf

TEST_WORKLOADS="
500m-btree-50r50u.wtperf${POSTFIX}
500m-btree-80r20u.wtperf${POSTFIX}
500m-btree-rdonly.wtperf${POSTFIX}
checkpoint-schema-race.wtperf${POSTFIX}
checkpoint-stress-schema-ops.wtperf${POSTFIX}
checkpoint-stress.wtperf${POSTFIX}
evict-btree-1.wtperf${POSTFIX}
evict-btree-stress-multi.wtperf${POSTFIX}
evict-btree-stress.wtperf${POSTFIX}
evict-btree.wtperf${POSTFIX}
evict-fairness.wtperf${POSTFIX}
evict-lsm-1.wtperf${POSTFIX}
evict-lsm.wtperf${POSTFIX}
index-pareto-btree.wtperf${POSTFIX}
insert-rmw.wtperf${POSTFIX}
large-lsm.wtperf${POSTFIX}
log.wtperf${POSTFIX}
long-txn-btree.wtperf${POSTFIX}
long-txn-lsm.wtperf${POSTFIX}
medium-btree.wtperf${POSTFIX}
medium-lsm-compact.wtperf${POSTFIX}
medium-lsm.wtperf${POSTFIX}
medium-multi-btree-log-partial.wtperf${POSTFIX}
medium-multi-btree-log.wtperf${POSTFIX}
medium-multi-lsm-noprefix.wtperf${POSTFIX}
medium-multi-lsm.wtperf${POSTFIX}
modify-force-update-large-record-btree.wtperf${POSTFIX}
modify-large-record-btree.wtperf${POSTFIX}
mongodb-large-oplog.wtperf${POSTFIX}
mongodb-oplog.wtperf${POSTFIX}
mongodb-secondary-apply.wtperf${POSTFIX}
mongodb-small-oplog.wtperf${POSTFIX}
overflow-10k.wtperf${POSTFIX}
overflow-130k.wtperf${POSTFIX}
small-btree.wtperf${POSTFIX}
small-lsm.wtperf${POSTFIX}
update-btree.wtperf${POSTFIX}
update-checkpoint-btree.wtperf${POSTFIX}
update-checkpoint-lsm.wtperf${POSTFIX}
update-delta-mix1.wtperf${POSTFIX}
update-delta-mix2.wtperf${POSTFIX}
update-delta-mix3.wtperf${POSTFIX}
update-grow-stress.wtperf${POSTFIX}
update-large-lsm.wtperf${POSTFIX}
update-large-record-btree.wtperf${POSTFIX}
update-lsm.wtperf${POSTFIX}
update-only-btree.wtperf${POSTFIX}
update-shrink-stress.wtperf${POSTFIX}"

TEST_BRANCH=wt-dev
#ORIG_BRANCH=wt-dev-morecache

if [[ "$OSTYPE" == *"darwin"* ]]; then
    TEST_BASE=${HOME}/Work/WiredTiger/WTPERF
else
#    TEST_BASE=/mnt/pmem/sasha
    TEST_BASE=/mnt/data0/sasha
fi

#
# Create the output directories
#
if [ ! -d ${HOME}/Work/WiredTiger/WTPERF ]; then
    mkdir ${HOME}/Work/WiredTiger/WTPERF
fi

if [ ! -d ${HOME}/Work/WiredTiger/WTPERF/OUTPUT ]; then
    mkdir ${HOME}/Work/WsiredTiger/WTPERF/OUTPUT
fi

OUTPUT_BASE=${HOME}/Work/WiredTiger/WTPERF/OUTPUT/${EXP_TAG}

if [ ! -d ${OUTPUT_BASE} ]; then
    mkdir ${OUTPUT_BASE}
fi

#for dest in ${TEST_BRANCH} ${ORIG_BRANCH};
for dest in ${TEST_BRANCH};
do
    if [ ! -d ${OUTPUT_BASE}/${dest} ]; then
        mkdir ${OUTPUT_BASE}/${dest}
    fi
done

# Run the workloads
#

for workload in ${TEST_WORKLOADS};
do
    #    for branch in ${TEST_BRANCH} ${ORIG_BRANCH};
    for branch in ${TEST_BRANCH};
    do
        # Run the test workload
        DB_HOME=${TEST_BASE}/WT_TEST

        echo ${workload} ${branch}

        cd ${HOME}/Work/WiredTiger/${branch}/build_posix/bench/wtperf

        for iter in {1..3};
        do
            rm -rf ${DB_HOME}/*
            echo Iteration ${iter}
	    # Populate the new database every time for 500m-btree workloads
	    if [[ "$workload" == *"500m-btree"* ]]; then
		./wtperf -h ${DB_HOME} -O ../../../bench/wtperf/runners/500m-btree-populate.wtperf${POSTFIX}
	    fi
            ./wtperf -h ${DB_HOME} -O ../../../bench/wtperf/runners/${workload}
	    # Save the configuration
	    cp ${DB_HOME}/CONFIG.wtperf ${OUTPUT_BASE}/${branch}/${workload}.config.${iter}
	    # Save the database file size
	    ls -lh ${DB_HOME}/*.wt > ${OUTPUT_BASE}/${branch}/${workload}.lsh.${iter}
            # Save the test results
            cp ${DB_HOME}/test.stat ${OUTPUT_BASE}/${branch}/${workload}.test.stat.${iter}
	    # Save any profiling output
	    if [ -f perf.data ]; then
		cp perf.data ${OUTPUT_BASE}/${branch}/${workload}.perf.data.${iter}
	    fi
            # Save the stats
            mkdir ${OUTPUT_BASE}/${branch}/${workload}.${iter}.STAT
            cp ${DB_HOME}/WiredTigerStat* ${OUTPUT_BASE}/${branch}/${workload}.${iter}.STAT/.
        done
    done
done


