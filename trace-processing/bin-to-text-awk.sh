#!/bin/sh

ls trace.bin.* | awk '{print "${HOME}/Work/DINAMITE/bintrace-toolkit/trace_parser -p print -m ./ " $1 " > "$1".txt"}'