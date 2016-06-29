#! /usr/bin/env python

# Print out proportions of "correct answers in first peak and first 5

import argparse
import os.path
import sys
import string
import numpy as np

class rangedescr(object):
    """Describe required range"""
    
    def __init__(self, lower, upper):
        
        self.lower = lower
        self.upper = upper
        self.asfirst = 0
        self.in5 = 0
    
    def checkrange(self, vals, hadmatch):
        """Bump count according to the numbers in range"""
        sel = (vals >= self.lower) & (vals <= self.upper)
        if sel[0]:
            self.asfirst += 1
        if not hadmatch and np.count_nonzero(sel) != 0:
            self.in5 += 1
            return True
        return hadmatch

# According to type of display select column, xlabel  for hist, ylabel for plot

parsearg = argparse.ArgumentParser(description='Print percentages of results in ranges', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('ranges', type=str, nargs='+', help='ranges as low:spread')
parsearg.add_argument('--infile', type=str, required=True, help='Input file of numbers')
parsearg.add_argument('--outfile', type=str, help='Output file if required, else display')


resargs = vars(parsearg.parse_args())
rangeargs = resargs['ranges']
infile = resargs['infile']
outfile = resargs['outfile']

restcount = 0

rangelist = []

try:
    inf = np.loadtxt(infile, unpack=True)
except IOError as e:
    print "Error loading input file", infile
    print "Error was", e.args[1]
    sys.exit(100)
except (ValueError,TypeError):
    print "Conversion error input file", infile
    sys.exit(101)

for ra in rangeargs:

    parts = string.split(ra, ':')
    if len(parts) != 2:
        print "Do not understand range arg", ra
        sys.exit(102)
    
    try:
        lows = float(parts[0])
        highs = float(parts[1])
    except ValueError:
        print "Expected numeric low/high at", ra
        sys.exit(103)
    
    lows, highs = (lows-highs, lows+highs)
    
    if lows >= highs:
        print "Invalid range in", ra
        sys.exit(104)
    
    rangelist.append(rangedescr(lows, highs))


for lin in inf:
    hadmatch = False
    for ra in rangelist:
        hadmatch = ra.checkrange(lin, hadmatch)

nlines = float(inf.shape[-1])

for ra in rangelist:
    print "%.0f %.0f" % (ra.asfirst * 100.0 / nlines, ra.in5 * 100.0 / nlines),
print
sys.exit(0)
