#! /usr/bin/env python

# AstroML parse table and generate periodogram

import argparse
import os
import os.path
import sys
import string
import numpy as np
import numpy.random as nr
from gatspy.periodic import LombScargle
import periodarg
import argmaxmin

parsearg = argparse.ArgumentParser(description='Extract Window Function using Gatspy and white noise', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('infile', type=str, nargs=1, help='Input Time/Intensity file')
parsearg.add_argument('--tcol', type=int, default=0, help='Column in input data for times')
parsearg.add_argument('--outspec', type=str, help='Output spectrum file', required=True)
parsearg.add_argument('--periods', type=str, help='Periods as start:step:stop or start:stop/number')
parsearg.add_argument('--error', type=float, default=.01, help='Error bar (if needed)')
parsearg.add_argument('--uniform', type=str, help='Use Uniform noise as low:high')
parsearg.add_argument('--gauss', type=str, help='Use Gaussian noise as mean:std')
parsearg.add_argument('--iters', type=int, default=100, help='Number of iterations')
parsearg.add_argument('--maxes', type=int, default=0, help='Limit on number of maxima to accum 0=none')

resargs = vars(parsearg.parse_args())

maxes = resargs['maxes']
err = resargs['error']
infile = resargs['infile'][0]
outspec = resargs['outspec']
try:
	periods = periodarg.optperiodrange(resargs['periods'])
except ValueError:
    sys.exit(10)
tcol = resargs['tcol']
gaussp = resargs['gauss']
uniformp = resargs['uniform']
iters = resargs['iters']

errors = 0

if infile is None or not os.path.isfile(infile):
    print "No input data file"
    errors += 1
    integ = "none"
if err <= 0.0:
    print "Error value must be +ve"
    errors += 1
if gaussp is None and uniformp is None:
	print "No error arg given"
	errors += 1

if gaussp is not None:
	try:
		gmean, gstd = map(lambda x:float(x), string.split(gaussp, ':'))
	except ValueError:
		print "Invalid gauss arg format", gaussp
		errors += 1
if uniformp is not None:
	try:
		ulow, uhigh = map(lambda x:float(x), string.split(uniformp, ':'))
	except ValueError:
		print "Invalid uniform arg format", uniformp
		errors += 1

if errors > 0:
    sys.exit(10)

# Load up array of timings

try:
    arr = np.loadtxt(infile, unpack=True)
    timings = arr[tcol]
    timings -= timings[0]
except IOError as e:
    print "Could not load integration file", integ, "error was", e.args[1]
    sys.exit(11)
except ValueError:
    print "Conversion error on", integ
    sys.exit(12)
except IndexError:
    print "Invalid data time column max =", arr.shape[0] 
    sys.exit(13)

results = np.zeros_like(periods)

for n in xrange(0,iters):
	sums = np.zeros_like(timings)
	if gaussp is not None:
		sums += nr.normal(loc=gmean, scale=gstd, size=len(timings))
	if uniformp is not None:
		sums += nr.uniform(low=ulow, high=uhigh, size=len(timings))
	model = LombScargle().fit(timings, sums, err)
	pgram = model.periodogram(periods)
	if maxes > 0:
		maxima = argmaxmin.maxmaxes(periods, pgram)
		if len(maxima) > maxes: maxima = maxima[0:maxes]
		results[maxima] += pgram[maxima]
	else:
		results += pgram
	print "Completed iteration", n+1

res = np.array([periods, results])

try:
    np.savetxt(outspec, res.transpose())
except IOError as e:
    print "Could not save output file", outspec, "error was", e.args[1]
    sys.exit(14)
