#! /usr/bin/env python

import argparse
import scipy.signal as ss
import numpy as np
import os.path
import os
import sys
import string
import rangearg
import argmaxmin
import miscutils

parsearg = argparse.ArgumentParser(description='Print top n maximum peak')
parsearg.add_argument('spec', type=str, nargs='+', help='Spectrum file(s)')
parsearg.add_argument('--maxnum', type=int, default=1, help='Number of maxima to take')
parsearg.add_argument('--plusint', action='store_true', help='Display intensity as well')
parsearg.add_argument('--filename', action='store_true', help='Display file name')
parsearg.add_argument('--aserror', type=float, default=0.0, help='Display as percentage error from')

resargs = vars(parsearg.parse_args())

specs = resargs['spec']
maxnum = resargs['maxnum']
plusint = resargs['plusint']
filename = resargs['filename']
aserror = resargs['aserror']

errors = 0

for spec in specs:
    try:
        periods, amps = np.loadtxt(spec, unpack=True)
    except IOError as e:
        sys.stdout = sys.stderr
        print "Could not load spectrum file", spec, "error was", e.args[1]
        sys.stdout = sys.__stdout__
        errors += 1
        continue
    
    rspec = miscutils.removesuffix(spec)
    maxima = argmaxmin.maxmaxes(periods, amps)
    
    # If that's too many, prune taking the largest
    
    if len(maxima) > maxnum: maxima = maxima[0:maxnum]
    
    if filename:
        print "%s:" % rspec,
    
    had = 0
    for m in maxima:
        if had > 0:
            print " ",
        had += 1
        pv = periods[m]
        if aserror != 0.0:
            pv = abs(pv - aserror) * 100.0 / aserror
        if plusint:
            print "%#.4g,%#.4g" % (pv, amps[m]),
        else:
            print "%#.4g" % pv,
    print

if errors > 0:
    sys.exit(10)
sys.exit(0)