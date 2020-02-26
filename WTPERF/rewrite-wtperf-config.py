#!/usr/bin/env python

import argparse
import os
import re
import sys

suppliedConfigPairs = [];
suppliedConfigSingles = [];

# Codes for various colors for printing of informational and error messages.
#
class color:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

#
# We expect a string of key=value pairs separated by commas.
# For example:
#        allocation_size=128k,internal_page_max=128k
#
def parse_new_table_config(newConfig):

    kv_pairs = newConfig.strip().split(",");

    print(color.BOLD + "New configuration string: " + color.END + newConfig);
    if (len(kv_pairs) < 2):
        suppliedConfigSingles.append(kv_pairs[0]);
        return 0;

    for kvpair in kv_pairs:
        if (len(kvpair) == 0):
            continue;

        kv = kvpair.split("=");
        if (len(kv) < 2):
            print("Invalid key-value pair in configuration: " + kvpair);
            return -1;
        else:
            print(str(kv[0]) + "=" + str(kv[1]));
            suppliedConfigPairs.append((kv[0], kv[1]));

    return 0;

def parseNL(numbersLetters):

    number = 0;
    letter = '';

    for w in numbersLetters:
        if (len(w) == 0):
            continue;
        if (w.isnumeric()):
            number = int(w);
        else:
            letter = w;

    return number, letter;

def getSizeMultiplier(s):

    s = s.upper();
    mult = 0;

    if (s == 'B'):
        mult = 1;
    elif (s == 'K'):
        mult = 1024;
    elif (s == 'M'):
        mult = 1024*1024;
    elif (s == 'G'):
        mult = 1024*1024*1024;

    return mult;

def compareAndChoose(old, new):

    oldNumbersLetters = re.split('(\d+)', old);
    newNumbersLetters = re.split('(\d+)', new);

    oldNumber, oldLetter = parseNL(oldNumbersLetters);
    newNumber, newLetter = parseNL(newNumbersLetters);

    oldSizeMultiplier = getSizeMultiplier(oldLetter);
    newSizeMultiplier = getSizeMultiplier(newLetter);

    if (oldNumber * oldSizeMultiplier > newNumber * newSizeMultiplier):
        return old;
    else:
        return new;

def modify(oldKVPair, newConfigPairs):

    oldKV = oldKVPair.split("=");

    # We don't support augmenting complex configuration strings.
    # Return as is.
    #
    if (len(oldKV) !=2):
        return oldKVPair;

    for idx, newKV in enumerate(newConfigPairs):
        if (newKV[0] != oldKV[0]):
            continue;

        winningValue = compareAndChoose(oldKV[1], newKV[1]);

        # We augmented this config option, so let's remove it,
        # otherwise it will be added as is.
        del newConfigPairs[idx];

        return oldKV[0] + "=" + winningValue;

    return oldKVPair;

def augmentConfigString(line, configStringName, newConfigPairs, newConfigSingles):

    newConfigWords = [];
    s = '';

    # Separate out the part of the string after the
    # initial configuration name and the equal sign.
    # We want to get to the actual value or key=value pairs.
    #
    configValueTokens = line.split(configStringName + "=");
    newConfigWords.append(configStringName + "=\"");

    # If we have a single configuration value, as opposed to key-value pairs,
    # treat it specially.
    #
    if (len(configValueTokens) == 1):
        w = ",";
        w = w.join(newConfigSingles);
        newConfigWords.append(w);
        newConfigWords.append("\"\n");
        return s.join(newConfigWords);

    # We do not support augmenting these complex strings.
    # Return as is.
    if (len(configValueTokens) != 2):
        print(color.BOLD + "Unexpected configuation string: "+ color.RED +
              line + color.END);
        return line;

    configValues = configValueTokens[1].strip().strip("\"");

    configKVPairs = configValues.split(",");
    for oldKV in configKVPairs:
        newKV = modify(oldKV, newConfigPairs);
        newConfigWords.append(newKV)
        newConfigWords.append(",");

    # Append all new configuration values that were given by the
    # user, but not found in the old file.
    for newKV in newConfigPairs:
        newConfigWords.append(newKV[0] + "=" + newKV[1]);
        newConfigWords.append(",");

    # Remove the last comma we added "
    del newConfigWords[-1];

    newConfigWords.append("\"\n");
    return s.join(newConfigWords);

def processFile(oldFileName, newFileName, configStringName):

    print(oldFileName + " --> " + newFileName);

    oldFile = open(oldFileName);
    newFile = open(newFileName, "w");

    # Create copies of new config values, because they will be
    # modified.
    newConfigPairs = suppliedConfigPairs.copy();
    newConfigSingles = suppliedConfigSingles.copy();

    lines = oldFile.readlines();
    for line in lines:
        if not line.startswith(configStringName):
            newFile.write(line);
        else:
            augmentedConfigString = augmentConfigString(line, configStringName,
                                                        newConfigPairs,
                                                        newConfigSingles);
            newFile.write(augmentedConfigString);

    oldFile.close();
    newFile.close();

def modify_files(files, newSuffix, configStringName):

    print(color.BOLD + "Processing files..." + color.END);

    for file in files:
        if (not os.path.exists(file)):
            print("File " + file + " does not exist.");
            return;

        fname_comps = file.split(".wtperf");
        newFileName = fname_comps[0] + "." + newSuffix + ".wtperf";
        processFile(file, newFileName, configStringName);

def main():

    parser = argparse.ArgumentParser(description=
                                 'Rewrite WTPERF table configuration.');
    parser.add_argument('files', type=str, nargs='*',
                        help='WTPERF configuration files to process');
    parser.add_argument('-n', '--name', dest='configStringName', default='',
                        help='Name of WTPERF config string that will be augmented.');
    parser.add_argument('-c', '--config', dest='configStringValue', default='',
                        help='WTPERF configuration string that will be \
                        augmented. If the new parameter is smaller \
                        than the old parameter, we will keep the old value.');
    parser.add_argument('-s', '--suffix', dest='newSuffix', default='new',
                        help='Suffix to add to names of the modified config files');

    args = parser.parse_args();

    if (len(args.files) == 0):
        parser.print_help();
        sys.exit(1);

    if (len(args.configStringName) == 0 or len(args.configStringValue) == 0):
        parser.print_help();
        sys.exit(1);

    if (parse_new_table_config(args.configStringValue) != 0):
        parser.print_help();
        sys.exit(1);

    modify_files(args.files, args.newSuffix, args.configStringName);

if __name__ == '__main__':
    main()
