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

resargs = vars(parsearg.parse_args())

specs = resargs['spec']
maxnum = resargs['maxnum']
plusint = resargs['plusint']

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
    
    print "%s:" % rspec,
    if plusint:
        for m in maxima:
            print "\t%#.4g,%#.4g" % (periods[m], amps[m]),
    else:
        for m in maxima:
            print "\t%.4g" % periods[m],
    print
