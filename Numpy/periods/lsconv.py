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
import periodarg

# According to type of display select column

optdict = dict(ew = 2, ps = 4, pr = 6)

parsearg = argparse.ArgumentParser(description='Perform L-S FFT', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('integ', type=str, nargs=1, help='Input integration file (time/intensity)')
parsearg.add_argument('--type', help='ew/ps/pr to select display', type=str, default="ew")
parsearg.add_argument('--outspec', type=str, help='Output spectrum file')
parsearg.add_argument('--nonorm', action='store_true', help='Do not normalise Y axis')
parsearg.add_argument('--periods', type=str, help='Periods as start:step:stop or start:stop/number')


resargs = vars(parsearg.parse_args())

integ = resargs['integ'][0]
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

tfreqs = 2 * np.pi / periods

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

# Generate result array

try:
    np.savetxt(outspec, np.transpose(np.array([periods, spectrum])))
except IOError as e:
    print "Could not save output file", outspec, "error was", e.args[1]
    sys.exit(13)
