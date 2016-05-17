#! /usr/bin/env python

# AstroML parse table and generate periodogram

import argparse
import os
import os.path
import sys
import numpy as np
import PyAstronomy.pyTiming.pyPeriod as pp
import PyAstronomy.pyTiming.pyPeriod.periodBase as pb
import periodarg

normdict = dict(s = 'Scargle', h = 'HorneBaliunas', c = 'Cumming', S = 'Scargle', H = 'HorneBaliunas', C = 'Cumming')

parsearg = argparse.ArgumentParser(description='Perform Gatspy L-S FFT', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('infile', type=str, nargs=1, help='Input Time/Intensity file')
parsearg.add_argument('--tcol', type=int, default=0, help='Column in input data for times')
parsearg.add_argument('--icol', type=int, default=1, help='Column in input data for intensity')
parsearg.add_argument('--outspec', type=str, help='Output spectrum file', required=True)
parsearg.add_argument('--periods', type=str, help='Periods as start:step:stop or start:stop/number')
parsearg.add_argument('--error', type=float, default=.01, help='Error bar (if needed)')
parsearg.add_argument('--normtype', type=str, default='h', help='Normalisation type, Scargle/HorneBaliunas/Cumming')
parsearg.add_argument('--ofac', type=int, default=10, help='Oversampling factor')
parsearg.add_argument('--hifac', type=float, default=1.0, help='Maximum frequency')
parsearg.add_argument('--abspower', action='store_true', help='Take abs value of powers')

resargs = vars(parsearg.parse_args())

try:
	normtype = normdict[resargs['normtype'][0]]
except KeyError:
	nomtype = 'HorneBaliunas'

err = resargs['error']
infile = resargs['infile'][0]
outspec = resargs['outspec']
try:
	periods = periodarg.optperiodrange(resargs['periods'])
except ValueError:
    sys.exit(10)
tcol = resargs['tcol']
icol = resargs['icol']
ofac = resargs['ofac']
hifac = resargs['hifac']

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

sums -= sums.mean()
timings -= timings[0]
tfreqs = 2 * np.pi / periods
ts = pb.TimeSeries(timings, sums, err)
pgram = pp.Gls(ts, freq=tfreqs, norm=normtype, ofac=ofac, hifac=hifac)
if resargs['abspower']:
	powers = np.abs(pgram.power)
else:
	powers = pgram.power
	powers[powers < 0.0] = 0.0
faps = np.array([pgram.FAP(p) for p in powers])

try:
    np.savetxt(outspec, np.transpose(np.array([periods, powers, faps])))
except IOError as e:
    print "Could not save output file", outspec, "error was", e.args[1]
    sys.exit(14)
