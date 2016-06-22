#!/bin/sh

FILE_NAME=""

if [ -z $1 ]; then
    echo "Please provide the file name for the archive"
    exit 1
else
    FILE_NAME=$1.tar
    echo The name of the archive will be $FILE_NAME
fi

rm *.gz
gzip log.txt.*

tar -cvf $FILE_NAME log.*.gz

scp $FILE_NAME sasha@ssh-linux.ece.ubc.ca:etc/www/download/.
