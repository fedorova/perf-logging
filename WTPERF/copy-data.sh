cp /mnt/ssd/sasha/WT_TEST/test.stat ycsb-b.wtperf.test.stat.2
mkdir ycsb-b.wtperf.2.STAT
cp -r /mnt/ssd/sasha/WT_TEST/WiredTigerStat.* ycsb-b.wtperf.2.STAT/.
cat /mnt/ssd/sasha/WT_TEST/WiredTiger.basecfg /mnt/ssd/sasha/WT_TEST/CONFIG.wtperf > ycsb-b.wtperf.config.2
free -h > ycsb-b.wtperf.free-h.2
du -sh /mnt/ssd/sasha/WT_TEST > ycsb-b.wtperf.disksize.2

