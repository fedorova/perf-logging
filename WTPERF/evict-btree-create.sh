WT_HOME=/cs/systems/home/fedorova/Work/WiredTiger/wt-dev/build_posix

DB_HOME=/tmpfs/WT_TEST

mkdir ${DB_HOME}
rm ${DB_HOME}/*


${WT_HOME}/bench/wtperf/wtperf -h ${DB_HOME} -O ./evict-btree-create.wtperf
