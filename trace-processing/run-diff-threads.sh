#!/bin/sh
WT_HOME=/cs/systems/home/fedorova/Work/WiredTiger/wt-fork/build_posix
#WT_HOME=/tmpfs/wt-fork/build_posix
DB_HOME=/tmpfs/WT_TEST/
OUTPUT_ROOT=/cs/systems/home/fedorova/Work/WiredTiger/WTPERF/EVICTION

for t in `seq 4 4 12`;
do
    EXPID=ORIG-MAR28-OCTAVIA-1EV-${t}T
    OUTPUT=${OUTPUT_ROOT}/TEST-STATS/${EXPID}
    mkdir ${OUTPUT}
#
    for i in `seq 1 3`;
    do
	mkdir ${OUTPUT}/${i}
	${WT_HOME}/bench/wtperf/wtperf -h ${DB_HOME} -O ./evict-btree-run.wtperf -o threads=\(\(count=${t},reads=1\)\) > num_spinners.txt
#
	mv ${DB_HOME}/test.stat ${OUTPUT}/${i}/.
	mv ${DB_HOME}/WiredTigerStat* ${OUTPUT}/${i}/.
	python ${WT_HOME}/../tools/wtstats/wtstats.py --clear ${OUTPUT}/${i}/WiredTigerStat*
	mv wtstats.html ${OUTPUT}/${i}/.
	mv num_spinners.txt ${OUTPUT}/${i}/.
    done
done







