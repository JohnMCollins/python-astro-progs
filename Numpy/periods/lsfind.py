#! /usr/bin/env python

# Integrate all of a spectrum starting from obs times file
# Obs times file is of form <spec file name> <obs time>

import argparse
import os
import os.path
import sys
import numpy as np
import string
import scipy.signal as ss
import scipy.integrate as si
import argmaxmin

# According to type of display select column

optdict = dict(ew = 1, ps = 2, pr = 3, lpr = 4)

parsearg = argparse.ArgumentParser(description='Perform L-S FFT and report peak periods')
parsearg.add_argument('integ', type=str, nargs='+', help='Input integration file(s) (time/intensity)')
parsearg.add_argument('--type', help='ew/ps/pr/lpr to select display', type=str, default="ew")
parsearg.add_argument('--out', type=str, help='Output result file')
parsearg.add_argument('--start', type=float, default=50, help='Starting point for range of periods')
parsearg.add_argument('--stop', type=float, default=100, help='End point for range of periods')
parsearg.add_argument('--step', type=float, default=.1, help='Step in range')

resargs = vars(parsearg.parse_args())

integ = resargs['integ']
outspec = resargs['out']
strt = resargs['start']
stop = resargs['stop']
step = resargs['step']

typeplot = resargs['type']

cols = [0,0,0,0]

for ty in string.split(typeplot, ','):
    try:
        c = optdict[string.lower(ty)]
        cols[c] = 1
    except KeyError:
        sys.stdout = sys.stderr
        print "Unknown type of plot", ty
        sys.exit(2)

errors = 0

if strt <= 0:
    sys.stdout = sys.stderr
    print "Cannot have -ve or zero start value"
    sys.exit(3)
if strt >= stop:
    sys.stdout = sys.stderr
    print "Start value > stop"
    sys.exit(4)

if outspec is not None:
    try:
        outf = open(outspec, 'a')
    except IOError as e:
        sys.stdout = sys.stderr
        print "Cannot open outpuf file", outspec, "error was", e.args[1]
        sys.exit(5)
    sys.stdout = outf

tdays = np.arange(strt, stop+step, step)
tfreqs = (2 * np.pi) / tdays
dayrange = np.max(tdays) - np.min(tdays)

for ifl in integ:

    # Load up array of timings/intensities

    try:
        arr = np.loadtxt(ifl, unpack=True)
    except IOError as e:
        sys.stdout = sys.stderr
        print "Could not load integration file", ifl, "error was", e.args[1]
        sys.exit(6)
    except ValueError:
        print "Conversion error on", ifl
        sys.exit(7)

    timings = arr[0]

    results = []
    for ycolumn in range(1,4):
        if not cols[ycolumn]: continue
        sums = arr[ycolumn]
        if np.min(sums) == np.max(sums):
            results.append(0.0)
            continue
        spectrum = ss.lombscargle(timings, sums, tfreqs)
        spectrum /= si.simps(spectrum, tdays) / dayrange

        maxes = argmaxmin.argrelmax(tdays, spectrum)
        if len(maxes) > 0:
            ret = np.argsort(spectrum[maxes])
            results.append(tdays[maxes[ret[-1]]])
        else:
            results.append(0.0)
    for r in results:
        print r,
    print

