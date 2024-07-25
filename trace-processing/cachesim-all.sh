#!/usr/bin/bash

# List of algorithms
algorithms=("lru" "lfu")

for algorithm in "${algorithms[@]}"
do
	./bin/cachesim /data/sasha/TRACES/ycsb-c-13GB-2GBcache-6min-traceBeforeEvict.cachesim.generic csv "$algorithm" 2259MB -t "time-col=1, obj-id-col=2, obj-size-col=3" > "$algorithm.out"
done


