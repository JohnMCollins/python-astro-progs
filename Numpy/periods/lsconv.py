#! /usr/bin/env python

# Integrate all of a spectrum starting from obs times file
# Obs times file is of form <spec file name> <obs time>

import argparse
import os
import os.path
import sys
import numpy as np
import re
import scipy.signal as ss
import scipy.integrate as si

# According to type of display select column, whether log

optdict = dict(ew = (1, False), ps = (2, False), pr = (3, True))

parsearg = argparse.ArgumentParser(description='Perform L-S FFT')
parsearg.add_argument('integ', type=str, nargs=1, help='Input integration file (time/intensity)')
parsearg.add_argument('--type', help='ew/ps/pr to select display', type=str, default="ew")
parsearg.add_argument('--logy', action='store_true', help='Take log of Y values')
parsearg.add_argument('--outspec', type=str, help='Output spectrum file')
parsearg.add_argument('--nonorm', action='store_true', help='Do not normalise Y axis')
parsearg.add_argument('--start', type=float, default=50, help='Starting point for range of periods')
parsearg.add_argument('--stop', type=float, default=100, help='End point for range of periods')
parsearg.add_argument('--step', type=float, default=.1, help='Step in range')

resargs = vars(parsearg.parse_args())

integ = resargs['integ'][0]
outspec = resargs['outspec']
strt = resargs['start']
stop = resargs['stop']
step = resargs['step']

typeplot = resargs['type']

try:
    ycolumn, logplot = optdict[typeplot]
except KeyError:
    print "Unknown type", typeplot, "specified"
    sys.exit(2)

errors = 0

if integ is None or not os.path.isfile(integ):
    print "No integration file"
    errors += 1
    integ = "none"
if outspec is None:
    print "No output spectrum file"
    errors += 1
if strt <= 0:
    print "Cannot have -ve or zero start value"
    errors += 1
if strt >= stop:
    print "Start value > stop"
    errors += 1

tdays = np.arange(strt, stop+step, step)
tfreqs = (2 * np.pi) / tdays

if errors > 0:
    sys.exit(10)

# Load up array of timings/intensities

try:
    arr = np.loadtxt(integ, unpack=True)
    timings = arr[0]
    sums = arr[ycolumn]
except IOError as e:
    print "Could not load integration file", integ, "error was", e.args[1]
    sys.exit(11)
except ValueError:
    print "Conversion error on", integ
    sys.exit(12)

if resargs['logy']:
    logplot = not logplot
if logplot:
    sums = np.log(sums)

# Do the business

spectrum = ss.lombscargle(timings, sums, tfreqs)

if not resargs['nonorm']:
    spectrum /= si.simps(spectrum, tdays) / (np.max(tdays) - np.min(tdays))

# Generate result array

try:
    np.savetxt(outspec, np.transpose(np.array([tdays, spectrum])))
except IOError as e:
    print "Could not save output file", outspec, "error was", e.args[1]
    sys.exit(13)
