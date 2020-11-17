#!/usr/bin/env python3

#
# Parses wtperf config file and returns the cache size in GB.
#

import argparse
from argparse import RawTextHelpFormatter
import re
import sys

def parse_file(fname):

    config_file = open(fname);
    lines = config_file.readlines();

    for line in lines:
        if not "cache_size" in line:
            continue;
        line = line[line.find("cache_size="):];
        tokens = line.split(",");

        tokens = tokens[0].split("=");

        cache_size = tokens[1];

        cache_size_num = int(re.search(r'\d+', cache_size).group());

        cache_size_units = re.search(r'\D+', cache_size).group().upper();

        if (cache_size_units.startswith("M")):
            cache_size_num = cache_size_num / 1000;
        elif (cache_size_units.startswith("K")):
            cache_size_num = cache_size_num / (1000*1000);

        return cache_size_num;

def main():

    parser = argparse.ArgumentParser(description=
                                     "Parse wtperf config file and extract the "
                                     "cache size in GB.",
                                     formatter_class=RawTextHelpFormatter);

    parser.add_argument('file', type=str, nargs=1,
                        help='WTPERF configuration file to process');

    args = parser.parse_args();

    if (len(args.file) == 0):
        parser.print_help();
        sys.exit(1);

    # Communicate the result to the caller via the exit code
    #
    exit_code =  parse_file(args.file[0]);
    sys.exit(exit_code);


if __name__ == '__main__':
    main()
