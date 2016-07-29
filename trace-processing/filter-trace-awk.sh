#!/bin/sh

for file in "$@"
do
    echo "grep $FILTER $file > $file.filtered" | sh
done
