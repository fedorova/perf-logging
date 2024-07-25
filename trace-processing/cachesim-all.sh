#!/usr/bin/bash

# List of algorithms
algorithms=("2Q" "ARC" "ARCv0" "Belady" "Cacheus" "Clock" "FIFO" "FIFOMERGE" "FIFO-REINSERTION" "GDSH" "Hyperbolic" "LECAR" "LECARv0" "LIRS" "LRU" "LFU" "LHD" "SIZE" "SLRU" "SLRUv0" "TinyFLU"}

for algorithm in "${algorithms[@]}"
do
	./bin/cachesim /data/sasha/TRACES/ycsb-c-13GB-2GBcache-6min-traceBeforeEvict.cachesim.generic csv "$algorithm" 2259MB -t "time-col=1, obj-id-col=2, obj-size-col=3" > "$algorithm.out"
	grep 'throughput' "$algorithm.out" | grep -o 'miss ratio [^,]*' | awk -v alg="$algorithm" '{print alg, $3}'
done


