#!/bin/bash

EXP_TAG="PMEM-2"

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
checkpoint-schema-race.wtperf
checkpoint-stress-schema-ops.wtperf
checkpoint-stress.wtperf
evict-btree-1.wtperf
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
medium-btree.wtperf
medium-lsm-compact.wtperf
medium-lsm.wtperf
medium-multi-btree-log-partial.wtperf
medium-multi-btree-log.wtperf
medium-multi-lsm-noprefix.wtperf
medium-multi-lsm.wtperf
modify-force-update-large-record-btree.wtperf
modify-large-record-btree.wtperf
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
500m-btree-50r50u.wtperf
500m-btree-80r20u.wtperf
500m-btree-rdonly.wtperf"

TEST_BRANCH=wt-dev
#ORIG_BRANCH=wt-dev-morecache

if [[ "$OSTYPE" == *"darwin"* ]]; then
    TEST_BASE=${HOME}/Work/WiredTiger/WTPERF
else
    TEST_BASE=/mnt/pmem/sasha
#    TEST_BASE=/mnt/ssd/sasha
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
export WIREDTIGER_CONFIG="mmap_all=true"
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
		./wtperf -h ${DB_HOME} -O ../../../bench/wtperf/runners/500m-btree-populate.wtperf
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


