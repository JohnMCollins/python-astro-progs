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

parsearg = argparse.ArgumentParser(description='Perform L-S FFT')
parsearg.add_argument('integ', type=str, nargs=1, help='Input integration file (time/intensity)')
parsearg.add_argument('--outspec', type=str, help='Output spectrum file')
parsearg.add_argument('--maxfile', type=str, help='Output maxima file')
parsearg.add_argument('--start', type=float, default=50, help='Starting point for range of periods')
parsearg.add_argument('--stop', type=float, default=100, help='End point for range of periods')
parsearg.add_argument('--step', type=float, default=.5, help='Step in range')

resargs = vars(parsearg.parse_args())

integ = resargs['integ'][0]
outspec = resargs['outspec']
maxfile = resargs['maxfile']
strt = resargs['start']
stop = resargs['stop']
step = resargs['step']

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
    timings, sums = np.loadtxt(integ, unpack=True)
except IOError as e:
    print "Could not load integration file", integ, "error was", e.args[1]
    sys.exit(11)
except ValueError:
    print "Conversion error on", integ
    sys.exit(12)

# Do the business

spectrum = ss.lombscargle(timings, sums, tfreqs)
periods = (2 * np.pi) / tfreqs

# Generate result array

try:
    np.savetxt(outspec, np.transpose(np.array([periods, spectrum])))
except IOError as e:
    print "Could not save output file", outspec, "error was", e.args[1]
    sys.exit(13)

if maxfile is not None:
	maxesat = ss.argrelmax(spectrum)[0]
	if len(maxesat) != 0:
		try:
			np.savetxt(maxfile, np.transpose(np.array([periods[maxesat], spectrum[maxesat]])))
		except IOError as e:
			print "Could not save maxima file", maxfile, "error was", e.args[1]
			sys.exit(14)

