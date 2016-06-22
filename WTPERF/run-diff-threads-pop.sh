WT_HOME=/cs/systems/home/fedorova/Work/WiredTiger/wt-fork/build_posix
DB_HOME=/tmpfs/WT_TEST

for t in `seq 96 1 96`;
do
    EXPID=WT-FORK-QUATCHI-POP-NO_T-6EV-FAIRLOCK-DEC31-${t}T
    OUTPUT=TEST-STATS/${EXPID}
    mkdir ${OUTPUT}
#
    for i in `seq 1 5`;
    do
	mkdir ${OUTPUT}/${i}
#	${WT_HOME}/bench/wtperf/wtperf -h ${DB_HOME} -O ./evict-btree-run.wtperf -o threads=\(\(count=${t},reads=1\)\)
#
	rm ${DB_HOME}/*
	${WT_HOME}/bench/wtperf/wtperf -h ${DB_HOME} -O ./parallel-pop-btree.wtperf -o populate_threads=${t}
	mv ${DB_HOME}/test.stat ${OUTPUT}/${i}/.
	mv ${DB_HOME}/WiredTigerStat* ${OUTPUT}/${i}/.
	python ${WT_HOME}/../tools/wtstats/wtstats.py --clear ${OUTPUT}/${i}/WiredTigerStat*
	mv wtstats.html ${OUTPUT}/${i}/.
    done
done







