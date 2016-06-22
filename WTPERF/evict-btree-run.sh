WT_DEV=/cs/systems/home/fedorova/Work/WiredTiger/wt-dev/build_posix
DB_HOME=/tmpfs/WT_TEST

if [ -z $1 ]; then
    WT_HOME=${WT_DEV}
else
    WT_HOME=$1
fi

echo Running from $WT_HOME

${WT_HOME}/bench/wtperf/wtperf -h ${DB_HOME} -O ./evict-btree-run.wtperf
