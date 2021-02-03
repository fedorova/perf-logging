#!/bin/bash
grep operations *.test.stat.* | grep -v "Executed 0" | grep -v "concurrent" | grep -v "checkpoint operations" | grep -v "scan operations" | grep -v complete
