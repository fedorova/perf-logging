#!/bin/bash

EXP_TAG="BASELINE"
POSTFIX=""
COMMAND_PREFIX=""

TEST_BRANCH=wt-6022
#ORIG_BRANCH=wt-dev-morecache

# For situation when I want to run as root, but
# have the output land in my home directory, set HOME explicitly
#
HOME=/home/sasha

export WIREDTIGER_CONFIG="statistics=(all)"
#export WIREDTIGER_CONFIG="statistics=(all),statistics_log=(sources=(\"file:\"))"

# We run this one explicitly before relevant workload benchmarks
#500m-btree-populate.wtperf

# These don't produce any interesting numbers
#mongodb-large-oplog.wtperf
#mongodb-oplog.wtperf
#mongodb-secondary-apply.wtperf
#mongodb-small-oplog.wtperf
#truncate-btree-populate.wtperf
#truncate-btree-workload.wtperf

TEST_WORKLOADS="
500m-btree-50r50u.wtperf${POSTFIX}
500m-btree-80r20u.wtperf${POSTFIX}
500m-btree-rdonly.wtperf${POSTFIX}
checkpoint-latency-0.wtperf
checkpoint-latency-1.wtperf
checkpoint-schema-race.wtperf${POSTFIX}
checkpoint-stress-schema-ops.wtperf${POSTFIX}
checkpoint-stress.wtperf${POSTFIX}
evict-btree-1.wtperf${POSTFIX}
evict-btree-readonly.wtperf${POSTFIX}
evict-btree-scan.wtperf${POSTFIX}
evict-btree-stress-multi.wtperf${POSTFIX}
evict-btree-stress.wtperf${POSTFIX}
evict-btree.wtperf${POSTFIX}
evict-fairness.wtperf${POSTFIX}
evict-lsm-1.wtperf${POSTFIX}
evict-lsm-readonly.wtperf${POSTFIX}
evict-lsm.wtperf${POSTFIX}
index-pareto-btree.wtperf${POSTFIX}
insert-rmw.wtperf${POSTFIX}
large-lsm.wtperf${POSTFIX}
log.wtperf${POSTFIX}
long-txn-btree.wtperf${POSTFIX}
long-txn-lsm.wtperf${POSTFIX}
many-table-stress.wtperf${POSTFIX}
medium-btree.wtperf${POSTFIX}
medium-lsm-async.wtperf${POSTFIX}
medium-lsm-compact.wtperf${POSTFIX}
medium-lsm.wtperf${POSTFIX}
medium-multi-btree-log-partial.wtperf${POSTFIX}
medium-multi-btree-log.wtperf${POSTFIX}
medium-multi-lsm-noprefix.wtperf${POSTFIX}
medium-multi-lsm.wtperf${POSTFIX}
metadata-split-test.wtperf${POSTFIX}
modify-force-update-large-record-btree.wtperf${POSTFIX}
modify-large-record-btree.wtperf${POSTFIX}
multi-btree-long.wtperf${POSTFIX}
multi-btree-read-heavy-stress.wtperf${POSTFIX}
multi-btree-stress.wtperf${POSTFIX}
multi-btree-zipfian-populate.wtperf${POSTFIX}
multi-btree-zipfian-workload.wtperf${POSTFIX}
multi-btree.wtperf${POSTFIX}
overflow-10k.wtperf${POSTFIX}
overflow-130k.wtperf${POSTFIX}
parallel-pop-btree.wtperf${POSTFIX}
parallel-pop-lsm.wtperf${POSTFIX}
parallel-pop-stress.wtperf${POSTFIX}
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

#TEST_WORKLOADS="
#evict-btree.wtperf${POSTFIX}
#evict-btree-readonly.wtperf${POSTFIX}"

if [[ "$OSTYPE" == *"darwin"* ]]; then
    TEST_BASE=${HOME}/Work/WiredTiger/WTPERF
else
#    TEST_BASE=/mnt/pmem/sasha
    TEST_BASE=/mnt/ssd/sasha
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

for workload in ${TEST_WORKLOADS};
do
    #    for branch in ${TEST_BRANCH} ${ORIG_BRANCH};
    for branch in ${TEST_BRANCH};
    do
        # Run the test workload
        DB_HOME=${TEST_BASE}/WT_TEST

        echo ${workload} ${branch}

        cd ${HOME}/Work/WiredTiger/${branch}/build_posix/bench/wtperf

        for iter in {1..2};
        do
	    # Drop caches
	    #
	    echo 3 > /proc/sys/vm/drop_caches

            rm -rf ${DB_HOME}/*
            echo Iteration ${iter}
	    #
	    # Populate the new database every time for 500m-btree read/write workloads
	    # We run the read-only workload after we ran both read/write workloads, so
	    # we don't populate the database for it.
	    #
	    if [[ "$workload" == 500m-btree-*r*u.* ]]; then
		${COMMAND_PREFIX} ./wtperf -h ${DB_HOME} -O ../../../bench/wtperf/runners/500m-btree-populate.wtperf${POSTFIX}
	    fi
	    #
	    # For the zipfian workload, run 'populate' before it executes
	    #
	    if [[ "$workload" == multi-btree-zipfian-workload.wtperf* ]]; then
		${COMMAND_PREFIX} ./wtperf -h ${DB_HOME} -O ../../../bench/wtperf/runners/multi-btree-zipfian-populate.wtperf${POSTFIX}
	    fi

	    #
	    # Run the workload
	    #
            ${COMMAND_PREFIX} ./wtperf -h ${DB_HOME} -O ../../../bench/wtperf/runners/${workload}

	    # Save the configuration
	    cp ${DB_HOME}/CONFIG.wtperf ${OUTPUT_BASE}/${branch}/${workload}.config.${iter}
	    cat ${DB_HOME}/WiredTiger.basecfg >> ${OUTPUT_BASE}/${branch}/${workload}.config.${iter}
	    # Save the amount of disk space used by the database
	    du -sh  ${DB_HOME} > ${OUTPUT_BASE}/${branch}/${workload}.disksize.${iter}
	    # Save the amount of page cache used by the benchmark
	    free -h > ${OUTPUT_BASE}/${branch}/${workload}.free-h.${iter}
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


