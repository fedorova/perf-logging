#!/bin/sh
#WT_HOME=/cs/systems/home/fedorova/Work/WiredTiger/wt-fork/build_posix
WT_HOME=/tmpfs/wt-fork-2544/build_posix
DB_HOME=/tmpfs/WT_TEST/
OUTPUT_ROOT=/cs/systems/home/fedorova/Work/WiredTiger/WTPERF/EVICTION

#for t in 8 16 48 64 96;
for t in 16;
do
    EXPNAME=WT-2544-QUATCHI-4EV-TIMING-MAY6
    EXPID=${EXPNAME}-${t}T
    OUTPUT=${OUTPUT_ROOT}/TEST-STATS/${EXPID}
    mkdir ${OUTPUT}
#
    for i in `seq 1 1`;
    do
	mkdir ${OUTPUT}/${i}
	${WT_HOME}/bench/wtperf/wtperf -h ${DB_HOME} -O ./evict-btree-run.wtperf -o threads=\(\(count=${t},reads=1\)\) 
#
		mv ${DB_HOME}/test.stat ${OUTPUT}/${i}/.
	mv ${DB_HOME}/WiredTigerStat* ${OUTPUT}/${i}/.
	python ${WT_HOME}/../tools/wtstats/wtstats.py --clear ${OUTPUT}/${i}/WiredTigerStat*
	mv wtstats.html ${OUTPUT}/${i}/.
    done
done

grep 'read oper' ${OUTPUT_ROOT}/TEST-STATS/${EXPNAME}*/*/test.stat
grep 'read oper' ${OUTPUT_ROOT}/TEST-STATS/${EXPNAME}*/*/test.stat | awk '{print $6}'







