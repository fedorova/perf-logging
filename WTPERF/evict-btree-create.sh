WT_HOME=$HOME/Work/WiredTiger/wt-dev/build_posix
DB_HOME=./WT_TEST
SCRIPTS_HOME=$HOME/Work/WiredTiger/perf-logging/WTPERF

mkdir ${DB_HOME}
rm ${DB_HOME}/*


${WT_HOME}/bench/wtperf/wtperf -h ${DB_HOME} -O ${SCRIPTS_HOME}/evict-btree-create.wtperf
