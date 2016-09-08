#!/usr/bin/python -tt

import sys
import argparse


#
# Arguments are two files: one is the summary file for the trace, the
# other one is the dot file for the synoptic chart. We parse the summary
# to figure out how much time the functions took to run relative to each
# other and augment the dot file to visually represent this information
# by using bright colours and large font sizes for time-consuming functions.
#

if __name__ == '__main__':
    main()
