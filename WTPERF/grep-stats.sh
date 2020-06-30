#!/bin/bash

for i; do
    echo Processing $i
    cd $i
    for entry in `ls $search_dir`; do
	echo Converting file $entry
	jq . < $entry > $entry.txt
    done
    cd ..
done
