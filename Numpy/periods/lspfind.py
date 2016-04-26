#! /usr/bin/env python

# AstroML parse table and generate periodogram

import argparse
import os
import os.path
import sys
import numpy as np
import scipy.signal as ss
import periodarg

parsearg = argparse.ArgumentParser(description='Perform Scipy L-S FFT', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('infile', type=str, nargs=1, help='Input Time/Intensity file')
parsearg.add_argument('--tcol', type=int, default=0, help='Column in input data for times')
parsearg.add_argument('--icol', type=int, default=1, help='Column in input data for intensity')
parsearg.add_argument('--outspec', type=str, help='Output spectrum file', required=True)
parsearg.add_argument('--periods', type=str, help='Periods as start:step:stop or start:stop/number')
parsearg.add_argument('--error', type=float, default=.01, help='Error bar (if needed)')
parsearg.add_argument('--sqamps', action='store_true', help='Square input amplitudes')
parsearg.add_argument('--rootres', action='store_true', help='Take root of results')

resargs = vars(parsearg.parse_args())

err = resargs['error']
infile = resargs['infile'][0]
outspec = resargs['outspec']
periods = resargs['periods']
if periods is None:
	try:
		periods = os.environ['PERIODS']
	except KeyError:
		periods = "1d:.01d:100d"
try:
    periods = periodarg.periodrange(periods)
except ValueError as e:
    print "Invalid period range", periods
    sys.exit(10)

tcol = resargs['tcol']
icol = resargs['icol']

errors = 0

if tcol == icol or tcol < 0 or icol < 0:
    print "Cannot understand column numnbers", tcol, "and", icol
    errors += 1
if infile is None or not os.path.isfile(infile):
    print "No input data file"
    errors += 1
    integ = "none"
if err <= 0.0:
    print "Error value must be +ve"
    errors += 1

if errors > 0:
    sys.exit(10)

# Load up array of timings/intensities

try:
    arr = np.loadtxt(infile, unpack=True)
    timings = arr[tcol]
    sums = arr[icol]
    if resargs['sqamps']:
        sums = np.square(sums)
except IOError as e:
    print "Could not load integration file", integ, "error was", e.args[1]
    sys.exit(11)
except ValueError:
    print "Conversion error on", integ
    sys.exit(12)
except IndexError:
    print "Invalid data column"
    sys.exit(13)

# Do the business

pgram = ss.lombscargle(timings, sums - sums.mean(), np.pi * 2.0/periods)

if resargs['rootres']:
    pgram = np.sqrt(pgram)

try:
    np.savetxt(outspec, np.transpose(np.array([periods, pgram])))
except IOError as e:
    print "Could not save output file", outspec, "error was", e.args[1]
    sys.exit(14)
