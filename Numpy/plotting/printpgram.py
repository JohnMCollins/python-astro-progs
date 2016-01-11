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
import math

parsearg = argparse.ArgumentParser(description='Print top n maximum peak', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('spec', type=str, nargs='+', help='Spectrum file(s)')
parsearg.add_argument('--maxnum', type=int, default=1, help='Number of maxima to take')
parsearg.add_argument('--plusint', action='store_true', help='Display intensity as well')
parsearg.add_argument('--latex', action='store_true', help='Put in Latex table boundaries')
parsearg.add_argument('--noendl', action='store_true', help='Dont put hlines in in latex mode')
parsearg.add_argument('--fcomps', type=str, help='Prefix by file name components going backwards thus 1:3')
parsearg.add_argument('--aserror', action='store_true', help='Display error only')
parsearg.add_argument('--errtot', action='store_true', help='Display error total')
parsearg.add_argument('--asdiff', type=float, default=0.0, help='Display difference as +/-')
parsearg.add_argument('--pcomp', type=int, help='Component of file names to compare periods with')
parsearg.add_argument('--prange', type=str, help='Range or periods to limit consideration to')
parsearg.add_argument('--prec', type=int, default=4, help='Precision')
parsearg.add_argument('--bfperc', type=float, default=-1.0, help='Render figure in bold if percent error <= value')

resargs = vars(parsearg.parse_args())

specs = resargs['spec']
maxnum = resargs['maxnum']
plusint = resargs['plusint']
asdiff = resargs['asdiff']
pcomp = resargs['pcomp']
prange = resargs['prange']
latex = resargs['latex']
prec = resargs['prec']
bfperc = resargs['bfperc']
aserror = resargs['aserror']
errtot = resargs['errtot']

if prange is not None:
    prange = rangearg.parserange(prange)
    if prange is None:
        sys.exit(19)

fmt = "%%.%df" % prec

fcomps = resargs['fcomps']
if fcomps is not None:
    try:
        fcomps = map(lambda x: -int(x), string.split(fcomps, ':'))
    except ValueError:
        sys.stdout = sys.stderr
        print "Cannot understand fcomps arg", fcomps
        sys.exit(20)
endl = ''
if latex:
    fcs = ' & '
    if not resargs['noendl']:
        endl =  ' \\\\\\hline'
    bfb = '\\textbf{'
    bfe = '}'
else:
    fcs = ' '
    bfb = bfe = '*'

errors = 0
errlist = []

for spec in specs:
    try:
        periods, amps = np.loadtxt(spec, unpack=True)
    except IOError as e:
        sys.stdout = sys.stderr
        print "Could not load spectrum file", spec, "error was", e.args[1]
        sys.stdout = sys.__stdout__
        errors += 1
        continue
    
    if prange is not None:
        sel = (periods >= prange[0]) & (periods <= prange[1])
        periods = periods[sel]
        amps = amps[sel]
        if len(periods) == 0:
            sys.stdout = sys.stderr
            print "No periods in given period range"
            sys.stdout = sys.__stdout
            errors += 1
            continue

    maxima = argmaxmin.maxmaxes(periods, amps)
    
    # If that's too many, prune taking the largest
    
    if len(maxima) > maxnum: maxima = maxima[0:maxnum]
    
    line = ''
    ewfbits = string.split(os.path.abspath(spec), '/')
    if fcomps is not None:
        pref = []
        for p in fcomps:
            try:
                c = ewfbits[p]
            except IndexError:
                c = ''
            pref.append(c)
        pref.append('')
        line = string.join(pref, fcs)
    
    pcompare = asdiff
    if pcompare is None or pcompare == 0.0:
        pcompare = None
        if pcomp is not None:
            try:
                pcompare = float(ewfbits[-pcomp])
            except ValueError, IndexError:
                pass
    had = 0
    for m in maxima:
        if had > 0:
            line += fcs
        had += 1
        pv = periods[m]
        if pcompare is not None:
            diff = abs(pv - pcompare)
            if aserror:
                nxt = fmt % diff
            else:
                nxt = fmt % pv
            errlist.append(diff)
            if diff * 100.0 / pcompare <= bfperc:
                nxt = bfb + nxt + bfe
            line += nxt
        else:
            if aserror != 0.0:
                pv = abs(pv - aserror) * 100.0 / aserror
            line += fmt % pv
        if plusint:
            line += "," + fmt % amps[m]
    print line + endl

if errtot and len(errlist) != 0:
    rmserr = math.sqrt((np.array(errlist)**2).sum()/len(errlist))
    pref = []
    pref.append('RMS')
    if fcomps is not None:
        for p in fcomps[1:]:
            pref.append('')
    pref.append(fmt % rmserr)
    print string.join(pref, fcs) + endl

if errors > 0:
    sys.exit(10)
sys.exit(0)