#!/bin/sh

synoptic.sh --dumpInvariants=true --dumpInitialPartitionGraph=true --noRefinement=true --noCoarsening=true --outputCountLabels=true  -c $HOME/Work/Perfume/synoptic/log-args.txt -o ./synoptic-output $@
