#!/bin/sh

synoptic.sh -v --dumpInvariants=true --dumpInitialPartitionGraph=true --noRefinement=true --noCoarsening=true --outputCountLabels=true --outputProbLabels=false  -o ./$@  $@
