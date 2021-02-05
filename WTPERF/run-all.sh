#!/bin/bash

ulimit -c unlimited

EXP_KIND="DRAM-LARGE"
MEMORY_LIMIT_GB=16
CACHE_SIZE_LIMIT_GB=`expr ${MEMORY_LIMIT_GB} - 4`
EXP_TAG=${MEMORY_LIMIT_GB}GB-${EXP_KIND}
POSTFIX=""
export MEMKIND_HOG_MEMORY=1

# Create a huge ramdisk file to limit the size of
# available DRAM. The amount of DRAM on howesound is about 188GB.
# To limit the amount of RAM to 16GB, I create a 172GB file on ramdisk
#
let block_count="(188 - ${MEMORY_LIMIT_GB}) * 1024"
echo "Creating a file on ramdisk with ${block_count} 1MB blocks"
dd < /dev/zero bs=1048576 count=${block_count} > /mnt/ramdisk/sasha/testfile
ls -lh /mnt/ramdisk/sasha

# Set the swapiness
sysctl vm.swappiness=100
echo "Set swappiness to..."
cat /proc/sys/vm/swappiness

echo "Checking the swap: "
swapon

TEST_BRANCH=wt-6022

# For situation when I want to run as root, but
# have the output land in my home directory, set HOME explicitly
#
if [[ "$OSTYPE" == *"linux"* ]]; then
    HOME=/home/sasha
fi

if [[ "$EXP_KIND" == *"DRAM"* ]]; then
    WIREDTIGER_BASE_CONFIG="statistics=(all)"
elif [[ "$EXP_KIND" == *"NVRAM"* ]]; then
    if [[ "$EXP_KIND" == *"NOWRITEALLOC"* ]]; then
	WIREDTIGER_BASE_CONFIG="statistics=(all),block_cache=[enabled=true,size=180GB,type=nvram,path=/mnt/pmem/sasha,hashsize=32768,system_ram=${MEMORY_LIMIT_GB}GB,percent_file_in_dram=50]"
    else
	WIREDTIGER_BASE_CONFIG="statistics=(all),block_cache=[enabled=true,size=180GB,type=nvram,path=/mnt/pmem/sasha,hashsize=32768,system_ram=${MEMORY_LIMIT_GB}GB,percent_file_in_dram=50,max_percent_overhead=10]"
    fi
fi

echo "Base config for $EXP_KIND experiment: $WIREDTIGER_BASE_CONFIG"

#export WIREDTIGER_BASE_CONFIG="statistics=(all),statistics_log=(sources=(\"file:\"))"
env

# We run this one explicitly before relevant workload benchmarks
#500m-btree-populate.wtperf

# These don't produce any interesting numbers. Some of them throttle operations.
#checkpoint-latency-0.wtperf${POSTFIX}
#checkpoint-stress.wtperf${POSTFIX}
#mongodb-large-oplog.wtperf
#mongodb-oplog.wtperf
#mongodb-secondary-apply.wtperf
#mongodb-small-oplog.wtperf
#truncate-btree-populate.wtperf
#truncate-btree-workload.wtperf

# Invalid configuration value
#checkpoint-latency-1.wtperf${POSTFIX}

# Periodically segfaults
#index-pareto-btree.wtperf

# Fail with errors.
#metadata-split-test.wtperf${POSTFIX}
#multi-btree-stress.wtperf${POSTFIX}
#multi-btree.wtperf${POSTFIX}

# This one is VERY long and uses little memory
#multi-btree-long.wtperf${POSTFIX}

# These use a very small amount of memory
#small-btree.wtperf${POSTFIX}
#small-lsm.wtperf${POSTFIX}

# This one fails with "Too many open files" error
#many-table-stress.wtperf${POSTFIX}

# Highly variable performance:
# medium-lsm-async.wtperf${POSTFIX}
# medium-multi-btree-log-partial.wtperf${POSTFIX}
# update-btree.wtperf
# update-checkpoint-lsm.wtperf${POSTFIX}
# update-lsm.wtperf

# Run faster with less memory
# modify-force-update-large-record-btree.wtperf${POSTFIX}
# update-large-record-btree.wtperf${POSTFIX}

TEST_WORKLOADS="
evict-btree-scan.wtperf${POSTFIX}
500m-btree-50r50u.wtperf${POSTFIX}
500m-btree-80r20u.wtperf${POSTFIX}
checkpoint-schema-race.wtperf${POSTFIX}
checkpoint-stress.wtperf${POSTFIX}
checkpoint-stress-schema-ops.wtperf${POSTFIX}
evict-btree.wtperf${POSTFIX}
evict-btree-1.wtperf${POSTFIX}
evict-btree-readonly.wtperf${POSTFIX}
evict-btree-stress.wtperf${POSTFIX}
evict-btree-stress-multi.wtperf${POSTFIX}
evict-fairness.wtperf${POSTFIX}
evict-lsm.wtperf${POSTFIX}
evict-lsm-1.wtperf${POSTFIX}
evict-lsm-readonly.wtperf${POSTFIX}
insert-rmw.wtperf${POSTFIX}
large-lsm.wtperf${POSTFIX}
long-txn-btree.wtperf${POSTFIX}
long-txn-lsm.wtperf${POSTFIX}
medium-btree.wtperf${POSTFIX}
medium-lsm.wtperf${POSTFIX}
medium-lsm-compact.wtperf${POSTFIX}
medium-multi-btree-log.wtperf${POSTFIX}
medium-multi-lsm.wtperf${POSTFIX}
medium-multi-lsm-noprefix.wtperf${POSTFIX}
modify-large-record-btree.wtperf${POSTFIX}
multi-btree-zipfian-populate.wtperf${POSTFIX}
multi-btree-zipfian-workload.wtperf${POSTFIX}
overflow-130k.wtperf${POSTFIX}
update-checkpoint-btree.wtperf${POSTFIX}
update-delta-mix1.wtperf${POSTFIX}
update-delta-mix2.wtperf${POSTFIX}
update-delta-mix3.wtperf${POSTFIX}
update-grow-stress.wtperf${POSTFIX}
update-shrink-stress.wtperf${POSTFIX}"

TEST_WORKLOADS="
checkpoint-stress-large.wtperf${POSTFIX}
evict-btree-large.wtperf${POSTFIX}
evict-btree-stress-multi-large.wtperf${POSTFIX}
medium-btree-large.wtperf${POSTFIX}
overflow-130k-large.wtperf${POSTFIX}
update-checkpoint-btree-large.wtperf${POSTFIX}
update-delta-mix1-large.wtperf${POSTFIX}
update-grow-stress-large.wtperf${POSTFIX}
large-lsm-large.wtperf${POSTFIX}
500m-btree-50r50u-large.wtperf${POSTFIX}"

if [[ "$OSTYPE" == *"darwin"* ]]; then
    TEST_BASE=${HOME}/Work/WiredTiger/WTPERF
else
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
echo Output stored in ${OUTPUT_BASE}

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

SCRIPT_HOME=$(pwd)

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

        cd /mnt/ssd/sasha/${branch}/build_posix/bench/wtperf

	# Save the commit version
	git show HEAD > ${OUTPUT_BASE}/${branch}/git.version

	unset WIREDTIGER_CONFIG
	export WIREDTIGER_CONFIG=${WIREDTIGER_BASE_CONFIG}

	# If we are memory-limiting, adjust the cache size to
	# correspond to the memory limit
	#
	${SCRIPT_HOME}/extract-cache-size.py ../../../bench/wtperf/runners/${workload}
	cache_size=$?

	echo Original cache size: $cache_size GB
	if [ "$cache_size" -gt "${CACHE_SIZE_LIMIT_GB}" ]; then
	    echo Changing to ${CACHE_SIZE_LIMIT_GB} GB
	    export WIREDTIGER_CONFIG=${WIREDTIGER_CONFIG},"cache_size=${CACHE_SIZE_LIMIT_GB}G"
	else
	    echo "Leaving cache size unchanged..."
	fi
	echo $WIREDTIGER_CONFIG

        for iter in {1..2};
        do
	    # Drop caches
	    #
	    echo 3 > /proc/sys/vm/drop_caches
	    free -h

            rm -rf ${DB_HOME}/*
            echo Iteration ${iter}
	    #
	    # Populate the new database every time for 500m-btree workloads. Otherwise we
	    # get unpredictable results.
	    #
	    if [[ "$workload" == 500m-btree* ]]; then
		if [[ "$workload" == *large* ]]; then
		    echo "running 500m-btree-populate-large.wtperf"
		    ./wtperf -h ${DB_HOME} -O ../../../bench/wtperf/runners/500m-btree-populate-large.wtperf${POSTFIX}
		    cp ${DB_HOME}/CONFIG.wtperf ${OUTPUT_BASE}/${branch}/${workload}.populate.config.${iter}
		    cp ${DB_HOME}/test.stat ${OUTPUT_BASE}/${branch}/${workload}.populate.test.${iter}
		else
		    ./wtperf -h ${DB_HOME} -O ../../../bench/wtperf/runners/500m-btree-populate.wtperf${POSTFIX}
		fi
	    fi
	    #
	    # For the zipfian workload, run 'populate' before it executes
	    #
	    if [[ "$workload" == multi-btree-zipfian-workload.wtperf* ]]; then
		./wtperf -h ${DB_HOME} -O ../../../bench/wtperf/runners/multi-btree-zipfian-populate.wtperf${POSTFIX}
	    fi

	    #
	    # Run the workload
	    #
            ${COMMAND_PREFIX} ./wtperf -h ${DB_HOME} -O ../../../bench/wtperf/runners/${workload} &
	    pid="$!"
	    echo "Waiting for pid $pid"
	    wait $pid

	    # Save the configuration
	    echo $pid > ${OUTPUT_BASE}/${branch}/${workload}.${pid}.${iter}
	    mv core ${workload}.${pid}.${iter}.core

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


# Reset swappiness to a normal value
sysctl vm.swappiness=10
