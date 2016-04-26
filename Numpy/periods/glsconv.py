#! /usr/bin/env python

# Gatspy version of LSCONV

import argparse
import os
import os.path
import sys
import numpy as np
from gatspy.periodic import LombScargle
import periodarg

# According to type of display select column

optdict = dict(ew = 2, ps = 4, pr = 6)

parsearg = argparse.ArgumentParser(description='Perform Gatspy L-S FFT', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('integ', type=str, nargs=1, help='Input integration file (time/intensity)')
parsearg.add_argument('--type', help='ew/ps/pr/lpr to select display', type=str, default="ew")
parsearg.add_argument('--outspec', type=str, help='Output spectrum file')
parsearg.add_argument('--periods', type=str, help='Periods as start:step:stop or start:stop/number')
parsearg.add_argument('--error', type=float, default=.01, help='Error bar')
parsearg.add_argument('--sqamps', action='store_true', help='Square input amplitudes')
parsearg.add_argument('--rootres', action='store_true', help='Take root of results')

resargs = vars(parsearg.parse_args())

err = resargs['error']
integ = resargs['integ'][0]
outspec = resargs['outspec']
try:
	periods = periodarg.optperiodrange(resargs['periods'])
except ValueError:
    sys.exit(10)

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
if err <= 0.0:
    print "Error value must be +ve"
    errors += 1

if errors > 0:
    sys.exit(10)

# Load up array of timings/intensities

try:
    arr = np.loadtxt(integ, unpack=True)
    timings = arr[1]
    sums = arr[ycolumn]
    if resargs['sqamps']:
        sums = np.square(sums)
except IOError as e:
    print "Could not load integration file", integ, "error was", e.args[1]
    sys.exit(11)
except ValueError:
    print "Conversion error on", integ
    sys.exit(12)

# Do the business

model = LombScargle().fit(timings, sums, err)
pgram = model.periodogram(periods)
if resargs['rootres']:
    pgram = np.sqrt(pgram)

try:
    np.savetxt(outspec, np.transpose(np.array([periods, pgram])))
except IOError as e:
    print "Could not save output file", outspec, "error was", e.args[1]
    sys.exit(13)
