#! /usr/bin/env python

# Get maxima from a set of files

import argparse
import os.path
import sys
import string
import math
import numpy as np
import matplotlib.pyplot as plt

def rplaces(n, up):
    """Round n up or down to global places places"""
    global places
    if places < -100: return n
    if up:
        return math.ceil(n * 10.0**places) * 10**(-places)
    else:
        return math.floor(n * 10.0**places) * 10**(-places)

def prange(mn, mx):
    """Display a range argument"""
    rmn = rplaces(mn, False)
    rmx = rplaces(mx, True)
    if rmn == 0.0: return "%.6g" % rmx 
    return "%.6g,%.6g" % (rmn, rmx)

parsearg = argparse.ArgumentParser(description='Get maxima for histograms and plotting')
parsearg.add_argument('--histogram', action='store_true', help='Get results for histogram')
parsearg.add_argument('--bins', type=int, default=20, help='Histogram bins')
parsearg.add_argument('--places', type=int, default=-1000000, help='Specify decimal places')
parsearg.add_argument('--forcemin', type=str, help='Force minimum value')
parsearg.add_argument('--forcemax', type=str, help='Force maximum value')
parsearg.add_argument('--individual', action='store_true', help='Do files individually')
parsearg.add_argument('datafiles', type=str, nargs='+', help='X/Y spectra files')

res = vars(parsearg.parse_args())

ashist = res['histogram']
places = res['places']
forcemin = res['forcemin']
forcemax = res['forcemax']
indiv = res['individual']
datafiles = res['datafiles']

resultmin = []
resultmax = []

errors = 0

for f in datafiles:
    try:
        inp = np.loadtxt(f, unpack=True)
    except IOError as e:
        print "File", f, "gave error", e.args[1]
        errors += 1
        continue
    yvals = inp[1]
    if ashist:
        hgram = np.histogram(yvals, res['bins'])
        yvals = hgram[0]
    if forcemin is None:
        mn = np.min(yvals)
    else:
        mn = float(forcemin)
    if forcemax is None:
        mx = np.max(yvals)
    else:
        mx = float(forcemax)
    resultmin.append(mn)
    resultmax.append(mx)

if errors > 0:
    print "Aborting due to errors"
    sys.exit(10)

if indiv:
    for mm in zip(resultmin, resultmax):
        print prange(*mm)
else:
    print prange(np.min(resultmin), np.max(resultmax))
