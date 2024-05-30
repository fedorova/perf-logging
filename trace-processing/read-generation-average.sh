grep "Sim evicted" ycsb-c-6.5GBdb-2GBcache-2min.cachesim.2.out | awk '{print $13}' | sed 's/,//g' | awk '{sum += $1; count += 1} END {if (count > 0) print sum / count}'
