#!/usr/bin/env python2.7

import argparse
import os


def getPrefix(fname):

    words = fname.split(".dot");

    if (len(words) > 0):
        return words[0];
    else:
        return None;

def main():

    parser = argparse.ArgumentParser(description=
                                 'Process performance log files');
    parser.add_argument('files', type=str, nargs='*',
                        help='log files to process');
    args = parser.parse_args();

    for fname in args.files:

        prefix = getPrefix(fname);

        if (prefix is None):
            print(fname + " does not seem to be a dot file");
            continue;

        imageFileName = prefix + ".png";
        mapFileName   = prefix + ".cmapx";


        print("Saving graph image to: " + imageFileName + "... "),
        ret = os.system("dot -Tpng " + fname + " > " + imageFileName);
        if (ret == 0):
            print("Success!");
        else:
            print("Failed...");

        print("Saving image map to: " + mapFileName + "... "),
        ret = os.system("dot -Tcmapx " + fname + " > " + mapFileName);
        if (ret == 0):
            print("Success!");
        else:
            print("Failed...");

if __name__ == '__main__':
    main()
