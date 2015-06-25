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

# According to type of display select column

optdict = dict(ew = 2, ps = 4, pr = 6)

parsearg = argparse.ArgumentParser(description='Perform L-S FFT')
parsearg.add_argument('integ', type=str, nargs=1, help='Input integration file (time/intensity)')
parsearg.add_argument('--type', help='ew/ps/pr to select display', type=str, default="ew")
parsearg.add_argument('--outspec', type=str, help='Output spectrum file')
parsearg.add_argument('--nonorm', action='store_true', help='Do not normalise Y axis')
parsearg.add_argument('--start', type=float, default=1, help='Starting point for range of periods')
parsearg.add_argument('--stop', type=float, default=100, help='End point for range of periods')
parsearg.add_argument('--steps', type=int, default=1000, help='Number of trials')
parsearg.add_argument('--byperiod', action='store_true', help='Do trials by period not frequency')

resargs = vars(parsearg.parse_args())

integ = resargs['integ'][0]
outspec = resargs['outspec']
strt = resargs['start']
stop = resargs['stop']
steps = resargs['steps']

typeplot = resargs['type']

try:
    ycolumn = optdict[typeplot]
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

if resargs['byperiod']:
    tperiods = np.linspace(stop, strt, steps)
    tfreqs = 2 * np.pi / tperiods
else:

    # I did get these round the right way.....

    start_freq = 2 * np.pi / stop
    stop_freq = 2 * np.pi / strt
    tfreqs = np.linspace(start_freq, stop_freq, steps)

if errors > 0:
    sys.exit(10)

# Load up array of timings/intensities

try:
    arr = np.loadtxt(integ, unpack=True)
    timings = arr[1]                    # Choosing Barycentric date
    sums = arr[ycolumn]
except IOError as e:
    print "Could not load integration file", integ, "error was", e.args[1]
    sys.exit(11)
except ValueError:
    print "Conversion error on", integ
    sys.exit(12)

# Do the business

spectrum = ss.lombscargle(timings, sums - sums.mean(), tfreqs)

if not resargs['nonorm']:
    spectrum = np.sqrt(spectrum * 4.0 / float(len(timings)))

tdays = 2.0 * np.pi / tfreqs

# Generate result array

try:
    np.savetxt(outspec, np.transpose(np.array([tdays, spectrum])))
except IOError as e:
    print "Could not save output file", outspec, "error was", e.args[1]
    sys.exit(13)
