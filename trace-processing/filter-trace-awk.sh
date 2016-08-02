#!/bin/sh

for file in "$@"
do
    echo "grep $FILTER $file > $file.filtered.$FILTER" | sh
done
