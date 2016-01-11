#! /usr/bin/env python

import sys
import os
import os.path
import re
import string
import argparse
import numpy as np
import jdate

parsearg = argparse.ArgumentParser(description='Prune ew file to remove outlying entries', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('ewfil', type=str, help='EW file', nargs='+')
parsearg.add_argument('--lower', type=float, default=2.0, help='Prune EWs this less than mean')
parsearg.add_argument('--upper', type=float, default=2.0, help='Prune EWs this greater than mean')

res = vars(parsearg.parse_args())

ewfiles = res['ewfil']
lowerlim = res['lower']
upperlim = res['upper']

if len(ewfiles) > 2:
    sys.stdout = sys.stderr
    print "Expecting at most 2 files"
    sys.exit(1)

if len(ewfiles) == 2:
    infile, outfile = ewfiles
else:
    infile = outfile = ewfiles[0]

try:
    inp = np.loadtxt(infile, unpack=True)
except IOError as e:
    sys.stdout = sys.stderr
    print "Error loading EW file", infile
    print "Error was", e.args[1]
    sys.exit(102)

if inp.shape[0] < 8:
    print "Expecting new format 8-column shape, please convert"
    print "Shape was", inp.shape
    sys.exit(103)

ews = inp[2]
dates = inp[0]

removed_dates = np.array([], dtype=np.float64)

orign = len(ews)

mv = ews.mean()
stv = ews.std()

sel = (ews - mv) > - lowerlim * stv
inp = inp[:,sel]
removed_dates = np.concatenate((removed_dates, dates[~sel]))
ews = inp[2]
dates = inp[0]
afterlower = len(ews)

sel = (ews - mv) < upperlim * stv
inp = inp[:,sel]
removed_dates = np.concatenate((removed_dates, dates[~sel]))
ews = inp[2]
dates = inp[0]
afterupper = len(ews)

print "%d originally %d removed as being < lower %d removed as being >  upper" % (orign, orign-afterlower, afterlower-afterupper)
if len(removed_dates) != 0:
    np.sort(removed_dates)
    for d in removed_dates:
        print jdate.display(d)

try:
    np.savetxt(outfile, np.transpose(inp))
except IOError as e:
    sys.stdout = sys.stderr
    print "Error saving EW file", infile
    print "Error was", e.args[1]
    sys.exit(103)
