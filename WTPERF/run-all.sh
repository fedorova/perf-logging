#!/bin/bash

#500m-btree-populate.wtperf
#500m-btree-rdonly.wtperf
#checkpoint-latency-0.wtperf
#checkpoint-latency-1.wtperf
#checkpoint-schema-race.wtperf
#checkpoint-stress-schema-ops.wtperf
#checkpoint-stress.wtperf
#evict-btree-scan.wtperf
#evict-lsm-readonly.wtperf
#medium-lsm-async.wtperf
#mongodb-large-oplog.wtperf
#mongodb-oplog.wtperf
#mongodb-secondary-apply.wtperf
#mongodb-small-oplog.wtperf
#multi-btree-long.wtperf
#multi-btree.wtperf
#parallel-pop-btree.wtperf
#parallel-pop-lsm.wtperf
#parallel-pop-stress.wtperf#
#truncate-btree-populate.wtperf
#truncate-btree-workload.wtperf

TEST_WORKLOADS="
500m-btree-50r50u.wtperf
500m-btree-80r20u.wtperf
evict-btree-1.wtperf
evict-btree-readonly.wtperf
evict-btree-stress-multi.wtperf
evict-btree-stress.wtperf
evict-btree.wtperf
evict-fairness.wtperf
evict-lsm-1.wtperf
evict-lsm.wtperf
index-pareto-btree.wtperf
insert-rmw.wtperf
large-lsm.wtperf
log.wtperf
long-txn-btree.wtperf
long-txn-lsm.wtperf
many-table-stress.wtperf
medium-btree.wtperf
medium-lsm-compact.wtperf
medium-lsm.wtperf
medium-multi-btree-log-partial.wtperf
medium-multi-btree-log.wtperf
medium-multi-lsm-noprefix.wtperf
medium-multi-lsm.wtperf
metadata-split-test.wtperf
modify-force-update-large-record-btree.wtperf
modify-large-record-btree.wtperf
multi-btree-read-heavy-stress.wtperf
multi-btree-stress.wtperf
multi-btree-zipfian-populate.wtperf
multi-btree-zipfian-workload.wtperf
overflow-10k.wtperf
overflow-130k.wtperf
small-btree.wtperf
small-lsm.wtperf
update-btree.wtperf
update-checkpoint-btree.wtperf
update-checkpoint-lsm.wtperf
update-delta-mix1.wtperf
update-delta-mix2.wtperf
update-delta-mix3.wtperf
update-grow-stress.wtperf
update-large-lsm.wtperf
update-large-record-btree.wtperf
update-lsm.wtperf
update-only-btree.wtperf
update-shrink-stress.wtperf"

TEST_WORKLOADS="
index-pareto-btree.wtperf
insert-rmw.wtperf
log.wtperf
many-table-stress.wtperf
medium-multi-btree-log-partial.wtperf
medium-multi-lsm.wtperf
medium-multi-lsm-noprefix.wtperf
overflow-130k.wtperf
update-lsm.wtperf"

TEST_WORKLOADS="
update-shrink-stress.wtperf"

TEST_BRANCH=wt-5170-mods
TEST_ORIG_BRANCH=wt-5170-mmap
ORIG_BRANCH=wt-dev-orig

if [[ "$OSTYPE" == *"darwin"* ]]; then
    TEST_BASE=${HOME}/Work/WiredTiger/WTPERF
else
    TEST_BASE=/mnt/data0/sasha
fi

#
# Create the output directories
#
if [ ! -d ${HOME}/Work/WiredTiger/WTPERF ]; then
    mkdir ${HOME}/Work/WiredTiger/WTPERF
fi

if [ ! -d ${HOME}/Work/WiredTiger/WTPERF/OUTPUT ]; then
    mkdir ${HOME}/Work/WiredTiger/WTPERF/OUTPUT
fi

OUTPUT_BASE=${HOME}/Work/WiredTiger/WTPERF/OUTPUT

for dest in ${TEST_BRANCH} ${ORIG_BRANCH};
do
    if [ ! -d ${OUTPUT_BASE}/${dest} ]; then
        mkdir ${OUTPUT_BASE}/${dest}
    fi
done

#
# Create the workload home directories
#
for home in ${TEST_BRANCH} ${ORIG_BRANCH};
do
    if [ ! -d ${TEST_BASE}/${home} ]; then
        mkdir ${TEST_BASE}/${home}
    fi
done

# Run the workloads
#
for workload in ${TEST_WORKLOADS};
do
    for branch in ${ORIG_BRANCH} ${TEST_ORIG_BRANCH} ${TEST_BRANCH};
#    for branch in ${TEST_BRANCH} ${ORIG_BRANCH};
#    for branch in ${TEST_BRANCH};
    do
        # Run the test workload
        DB_HOME=${TEST_BASE}/${branch}

        echo ${workload} ${branch}

        cd ${HOME}/Work/WiredTiger/${branch}/build_posix/bench/wtperf

        for iter in 1 2 3;
        do
            rm -rf ${DB_HOME}/*
            echo Iteration ${iter}
	    # Populate the new database every time for 500m-btree workloads
	    if [[ "$workload" == *"500m-btree"* ]]; then
		./wtperf -h ${DB_HOME} -O ../../../bench/wtperf/runners/500m-btree-populate.wtperf
	    fi
            ./wtperf -h ${DB_HOME} -O ../../../bench/wtperf/runners/${workload}
            # Save the test results
            cp ${DB_HOME}/test.stat ${OUTPUT_BASE}/${branch}/${workload}.test.stat.${iter}
            # Save the stats
            mkdir ${OUTPUT_BASE}/${branch}/${workload}.${iter}.STAT
            cp ${DB_HOME}/WiredTigerStat* ${OUTPUT_BASE}/${branch}/${workload}.${iter}.STAT/.
        done
    done
done

