#!/usr/bin/python3

# Compares if two .hs files have the exact same scores
# Useful to know if two there was any new score between two files

from nhighlib import *
import sys
import os

def usage():
    print("usage: %s FILE1 FILE2" % sys.argv[0])

def run():
    if len(sys.argv) != 3:
        usage()
        sys.exit(1)
    scores1 = loadScores(sys.argv[1])
    scores2 = loadScores(sys.argv[2])
    print(scores1.table == scores2.table)

if __name__=='__main__':
    run()
