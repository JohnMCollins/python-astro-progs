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

enhlookup = dict(bold = '\\textbf{', italic = '\\textit{',
                 red = '\\textcolor{red}{', blue = '\\textcolor{blue}{', green = '\\textcolor{green}{')

parsearg = argparse.ArgumentParser(description='Print top n maximum peak', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('spec', type=str, nargs='+', help='Spectrum file(s)')
parsearg.add_argument('--maxnum', type=int, default=1, help='Number of maxima to take')
parsearg.add_argument('--plusint', action='store_true', help='Display intensity as well')
parsearg.add_argument('--latex', action='store_true', help='Put in Latex table boundaries')
parsearg.add_argument('--noendl', action='store_true', help='Dont put hlines in in latex mode')
parsearg.add_argument('--fcomps', type=str, help='Prefix by file name components going backwards thus 1:3')
parsearg.add_argument('--aserror', action='store_true', help='Display error only')
parsearg.add_argument('--errtot', action='store_true', help='Display error total')
parsearg.add_argument('--asdiff', type=float, nargs='*', help='Display difference as +/-')
parsearg.add_argument('--pcomp', type=int, help='Component of file names to compare periods with')
parsearg.add_argument('--prange', type=str, help='Range or periods to limit consideration to')
parsearg.add_argument('--prec', type=int, default=4, help='Precision')
parsearg.add_argument('--bfperc', type=float, default=-1.0, help='Render figure in bold if percent error <= value')
parsearg.add_argument('--bfenh', type=str, nargs='*', help='List of enhancements for bold face (latex only)')
parsearg.add_argument('--fap', action='store_true', help='Display False Alarm Probs')
parsearg.add_argument('--fapprec', default=2, type=int, help='Precison of FAPs')

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
bfenh = resargs['bfenh']
aserror = resargs['aserror']
errtot = resargs['errtot']
dispfap = resargs['fap']
fapprec = resargs['fapprec']

if prange is not None:
    prange = rangearg.parserange(prange)
    if prange is None:
        sys.exit(19)

fmt = "%%.%df" % prec
fapfmt = "%%.%dg" % fapprec

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
    bfb = []
    if bfenh is None:
        bfb = ['\\textbf{']
    else:
        for etype in bfenh:
            try:
                bfb.append(enhlookup[etype])
            except KeyError:
                bfb.append(enhlookup['red'])    
    if len(bfb) == 0:
        bfb.append('\\textbf{')
    bfe = '}'
else:
    fcs = ' '
    bfb = ['*']
    bfe = '*'

num_enh = len(bfb)
errors = 0
errlist = []

for spec in specs:
    try:
        f = np.loadtxt(spec, unpack=True)
        periods = f[0]
        amps = f[1]
        fap = None
        if dispfap: fap = f[2]
    except IOError as e:
        sys.stdout = sys.stderr
        print "Could not load spectrum file", spec, "error was", e.args[1]
        sys.stdout = sys.__stdout__
        errors += 1
        continue
    except ValueError:
        sys.stdout = sys.stderr
        print "Insufficent columns in data file", spec
        errors += 1
        continue
    
    if prange is not None:
        sel = (periods >= prange[0]) & (periods <= prange[1])
        periods = periods[sel]
        amps = amps[sel]
        if fap is not None:
            fap = fap[sel]
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
    if pcompare is None:
        if pcomp is not None:
            try:
                pcompare = [float(ewfbits[-pcomp])]
            except ValueError, IndexError:
                pass
    had = 0
    for m in maxima:
        if had > 0:
            line += fcs
        had += 1
        pv = periods[m]
        if pcompare is not None:
            for ne, pc in enumerate(pcompare):
                diff = abs(pv - pc)
                if aserror:
                    nxt = fmt % diff
                else:
                    nxt = fmt % pv
                errlist.append(diff)
                if diff * 100.0 / pc <= bfperc:
                    nxt = bfb[ne % num_enh] + nxt + bfe
                    break
            line += nxt
        else:
            if aserror != 0.0:
                pv = abs(pv - aserror) * 100.0 / aserror
            line += fmt % pv
        if plusint:
            line += "," + fmt % amps[m]
        if dispfap:
            line += fcs + fapfmt % fap[m]
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