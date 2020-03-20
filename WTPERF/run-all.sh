#!/bin/bash

EXP_TAG="NVRAM"

#500m-btree-populate.wtperf
#

#500m-btree-50r50u.wtperf
#500m-btree-80r20u.wtperf
#500m-btree-rdonly.wtperf

# DO NOT RUN THESE WORKLOADS
# These workloads crash
#
# checkpoint-latency-0.wtperf
# checkpoint-latency-1.wtperf
# evict-btree-readonly.wtperf
# evict-lsm-readonly.wtperf

# Runs out of space
#
# many-table-stress.wtperf

# Bug in the config-update script
#
# metadata-split-test.wtperf

# ?
# index-to-pareto.wtperf
# medium-lsm-async.wtperf

# These always produce the same number of ops/second
#
# mongodb-small-oplog.wtperf
# mongodb-large-oplog.wtperf
# mongodb-oplog.wtperf
# mongodb-secondary-apply.wtperf
#
# Takes 10 hours. Have to copy all content out of D0* directories.
# multi-btree-long.wtperf
#
# Need to copy output data from a bunch of directories.
# multi-btree.wtperf
# multi-btree-stress.wtperf
# multi-btree-zipfian-populate.wtperf
# multi-btree-zipfian-workload.wtperf
#
#
# Crashes for whatever reason.
# multi-btree-read-heavy-stress.wtperf
#
# These are okay. Removing for now, because
# they use compression by default.
#
# overflow-10k.wtperf
# overflow-130k.wtperf
#
# Others excluded either due to crash or not interesting for performance:
# checkpoint-stress-schema-ops.wtperf
# checkpoint-stress.wtperf
# large-lsm.wtperf
# parallel-pop-btree.wtperf
# parallel-pop-lsm.wtperf
# parallel-pop-stress.wtperf
#
# truncate-btree-populate.wtperf
# truncate-btree-workload.wtperf
#
#

TEST_WORKLOADS="
checkpoint-schema-race.wtperf
evict-btree-1.wtperf
evict-btree-stress-multi.wtperf
evict-btree-stress.wtperf
evict-btree.wtperf
evict-btree-scan.wtperf
evict-fairness.wtperf
evict-lsm-1.wtperf
evict-lsm.wtperf
insert-rmw.wtperf
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
update-large-record-btree.wtperf"

TEST_BRANCH=wt-dev
ORIG_BRANCH=wt-dev-compress

if [[ "$OSTYPE" == *"darwin"* ]]; then
    TEST_BASE=${HOME}/Work/WiredTiger/WTPERF
else
#    TEST_BASE=/altroot/sasha/WTPERF
    TEST_BASE=/mnt/pmem/sasha
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

for dest in ${TEST_BRANCH} ${ORIG_BRANCH};
do
    if [ ! -d ${OUTPUT_BASE}/${dest} ]; then
        mkdir ${OUTPUT_BASE}/${dest}
    fi
done

# Run the workloads
#
for workload in ${TEST_WORKLOADS};
do
#    for branch in ${ORIG_BRANCH} ${TEST_ORIG_BRANCH} ${TEST_BRANCH};
    for branch in ${TEST_BRANCH} ${ORIG_BRANCH};
#    for branch in ${TEST_BRANCH};
    do
        # Run the test workload
        DB_HOME=${TEST_BASE}/WT_TEST

        echo ${workload} ${branch}

        cd ${HOME}/Work/WiredTiger/${branch}/build_posix/bench/wtperf

        for iter in 1;
        do
            rm -rf ${DB_HOME}/*
            echo Iteration ${iter}
	    # Populate the new database every time for 500m-btree workloads
	    if [[ "$workload" == *"500m-btree"* ]]; then
		./wtperf -h ${DB_HOME} -O ../../../bench/wtperf/runners/500m-btree-populate.wtperf
	    fi
            perf record ./wtperf -h ${DB_HOME} -O ../../../bench/wtperf/runners/${workload}
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


