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

parsearg = argparse.ArgumentParser(description='Print top n maximum peak')
parsearg.add_argument('spec', type=str, nargs='+', help='Spectrum file(s)')
parsearg.add_argument('--maxnum', type=int, default=1, help='Number of maxima to take')
parsearg.add_argument('--plusint', action='store_true', help='Display intensity as well')
parsearg.add_argument('--latex', action='store_true', help='Put in Latex table boundaries')
parsearg.add_argument('--fcomps', type=str, help='Prefix by file name components going backwards thus 1:3')
parsearg.add_argument('--aserror', type=float, default=0.0, help='Display as percentage error from')
parsearg.add_argument('--asdiff', type=float, default=0.0, help='Display difference as +/-')

resargs = vars(parsearg.parse_args())

specs = resargs['spec']
maxnum = resargs['maxnum']
plusint = resargs['plusint']
aserror = resargs['aserror']
asdiff = resargs['asdiff']
latex = resargs['latex']

fcomps = resargs['fcomps']
if fcomps is not None:
    try:
        fcomps = map(lambda x: -int(x), string.split(fcomps, ':'))
    except ValueError:
        sys.stdout = sys.stderr
        print "Cannot understand fcomps arg", fcomps
        sys.exit(20)
if latex:
    fcs = ' & '
    endl =  ' \\\\\\hline'
else:
    fcs = ' '
    endl = ''

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
    
    
    maxima = argmaxmin.maxmaxes(periods, amps)
    
    # If that's too many, prune taking the largest
    
    if len(maxima) > maxnum: maxima = maxima[0:maxnum]
    
    line = ''
    if fcomps is not None:
        pref = []
        ewfbits = string.split(spec, '/')
        for p in fcomps:
            try:
                c = ewfbits[p]
            except IndexError:
                c = ''
            pref.append(c)
        pref.append('')
        line = string.join(pref, fcs)
    
    had = 0
    for m in maxima:
        if had > 0:
            line += fcs
        had += 1
        pv = periods[m]
        if asdiff != 0.0:
            line += "%#.4g" % pv
            diff = pv - asdiff
            if diff >= 0.0: line += '+'
            line += "%#.4g" % diff
        else:
            if aserror != 0.0:
                pv = abs(pv - aserror) * 100.0 / aserror
            line += "%#.4g" % pv
        if plusint:
            line += ",%#.4g" % amps[m]
    print line + endl

if errors > 0:
    sys.exit(10)
sys.exit(0)