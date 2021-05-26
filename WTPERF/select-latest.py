#!/usr/bin/env python3

import math

def showSelectionData(num):

    probDict = {}

    for i in range(1, num+1):
        probDict[i] = 0;

    print("MAX NUMBER: " + str(num));

    for i in range(1, num*num):
        item  = math.ceil(math.sqrt(i));
        probDict[item] = probDict[item] + 1;
        print(str(i) + ":\t" + str(math.ceil(math.sqrt(i))));

    print("Selection probability:");
    print("=======================");
    for i in range(1, num+1):
        print(str(i) + ":\t" + str(probDict[i]/(num*num)));

def main():

    maxNumber = 100;

    showSelectionData(maxNumber);

if __name__ == '__main__':
    main()
