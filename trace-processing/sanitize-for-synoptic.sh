#!/bin/sh

for file in "$@"
do
    echo "Cleaning file $file"
    grep -v 'lock' $file | grep -v 'evict candidates' | grep -v 'evict entries' > $file.sz
done