#! /usr/bin/env python

# Integrate the H alpha peaks to get figures for the total values,
# assume continuum is normalised at 1 unless otherwise specified

import argparse
import os.path
import sys
import string
import numpy as np

# According to type of display select column, xlabel  for hist, ylabel for plot

parsearg = argparse.ArgumentParser(description='Select required numeric columns from data', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('cols', type=int, nargs='+', help='Required columns zero based')
parsearg.add_argument('--infile', type=str, help='Input file', required=True)
parsearg.add_argument('--outfile', type=str, help='Output file', required=True)
parsearg.add_argument('--format', type=str, default='%.18e', help='Format for columns')
parsearg.add_argument('--subfirst', action='store_true', help='Subtract first column first element from rest')

resargs = vars(parsearg.parse_args())
cols = resargs['cols']
infile = resargs['infile']
outfile = resargs['outfile']
format = resargs['format']
subfirst = resargs['subfirst']

try:
    inp = np.loadtxt(infile, unpack=True)
except IOError as e:
    print "Error loading input file", infile
    print "Error was", e.args[1]
    sys.exit(102)

selected = inp[cols]
if subfirst:
    selected[0] -= selected[0][0]

try:
    np.savetxt(outfile, selected.transpose(), fmt=format)
except IOError as e:
    print "Could not write output file", outfile
    print "Error was", e.args[1]
    sys.exit(103)

if inp.shape[0] < 8:
    print "Expecting new format 8-column shape, please convert"
    print "Shape was", inp.shape
    sys.exit(103)
