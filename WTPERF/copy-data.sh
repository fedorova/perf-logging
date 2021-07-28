cp /mnt/ssd/sasha/WT_TEST/test.stat ycsb-c.wtperf.test.stat.2
mkdir ycsb-c.wtperf.2.STAT
cp -r /mnt/ssd/sasha/WT_TEST/WiredTigerStat.* ycsb-c.wtperf.2.STAT/.
cat /mnt/ssd/sasha/WT_TEST/WiredTiger.basecfg /mnt/ssd/sasha/WT_TEST/CONFIG.wtperf > ycsb-c.wtperf.config.2
free -h > ycsb-c.wtperf.free-h.2
du -sh /mnt/ssd/sasha/WT_TEST > ycsb-c.wtperf.disksize.2

