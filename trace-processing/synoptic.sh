#!/bin/sh

# Runs Synoptic from the compiled class files, passing all command
# line argument directly to main().

SYNOPTIC=$HOME/Work/Perfume/synoptic

echo "Classpath prefix is $SYNOPTIC"
java -Xmx32g -XX:+UseG1GC -ea -cp $SYNOPTIC/lib/*:$SYNOPTIC/synoptic/bin/:$SYNOPTIC/daikonizer/bin/ synoptic.main.SynopticMain $*
