#! /usr/bin/env python

import argparse
import scipy.signal as ss
import scipy.integrate as si
import numpy as np
import string
import sys
import os
import glob
import datarange
import equivwidth
import meanval
import fakeobs

parsearg = argparse.ArgumentParser(description='Compute ew and subpeak profiles from specified ranges',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('spec', type=str, help='Spectrum files', nargs='+')
parsearg.add_argument('--glob', action='store_true', help='Apply glob to arguments')
parsearg.add_argument('--obstimes', type=str, help='File for observation times')
parsearg.add_argument('--otsuff', type=str, help='Suffix to add to file names in obs time file')
parsearg.add_argument('--xcolumn', help='Column in data for X values', type=int, default=0)
parsearg.add_argument('--ycolumn', help='Column in data for Y values', type=int, default=1)
parsearg.add_argument('--harange', type=str, help='H Alpha range', required=True)
parsearg.add_argument('--integ1', type=str, help='Blue horn range', required=True)
parsearg.add_argument('--integ2', type=str, help='Blue horn range', required=True)
parsearg.add_argument('--outfile', type=str, help='Output file')

resargs = vars(parsearg.parse_args())

spec = resargs['spec']

if resargs['glob']:
    sfs = spec
    spec = []
    for sf in sfs:
        gs = glob.glob(sf)
        gs.sort()
        spec.extend(gs)

xcolumn = resargs['xcolumn']
ycolumn = resargs['ycolumn']

harangename = resargs['harange']
integ1name = resargs['integ1']
integ2name = resargs['integ2']

try:
    harange = datarange.ParseArg(harangename)
    integ1 = datarange.ParseArg(integ1name)
    integ2 = datarange.ParseArg(integ2name)
except datarange.DataRangeError as e:
    print "Cannot parse range"
    print "Error was", e.args[0]
    sys.exit(10)

outew = resargs['outfile']

if outew is None:
    print "No ew file out given"
    sys.exit(5)

obstimes = dict()
obstimefile = resargs['obstimes']    
if obstimefile is None:
    print "No obs times file given"
    sys.exit(208)
obstimes = fakeobs.getfakeobs(obstimefile, resargs['otsuff'])
if obstimes is None:
    print "Cannot read fake obs file", obstimefile
    sys.exit(209)
if xcolumn == ycolumn:
    print "Cannot have X and Y columns the same"
    sys.exit(210)

results = []
errors = 0
nohorns = 0

for sf in spec:
    try:
        arr = np.loadtxt(sf, unpack=True)
        wavelengths = arr[xcolumn]
        amps = arr[ycolumn]
    except IOError as e:
        print "Could not load spectrum file", sf, "error was", e.args[1]
        sys.exit(211)
    except ValueError:
        print "Conversion error on", sf
        sys.exit(212)
    except IndexError:
        print "Do not believe columns x column", xcolumn, "y column", ycolumn
        sys.exit(213)
            
    obst = obstimes[sf]
    
    ew = equivwidth.equivalent_width(harange, wavelengths, amps)
    peak1w, peak1s = meanval.mean_value(integ1, wavelengths, amps)
    peak2w, peak2s = meanval.mean_value(integ2, wavelengths, amps)
    hr = (peak2s * peak1w) / (peak1s * peak2w)
    hs = equivwidth.equivalent_width(integ2, wavelengths, amps) / equivwidth.equivalent_width(integ1, wavelengths, amps)
    results.append([obst, obst, ew, 0.0, hs, 0.0, hr, 0.0])

results = np.array(results)

np.savetxt(outew, results)
