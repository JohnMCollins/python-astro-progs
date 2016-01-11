#! /usr/bin/env python

# Analyse results of running repeated periodicity scans

import sys
import os
import string
import re
import os.path
import math
import argparse
import numpy as np

def rootms(vals, n):
    """Return root mean square difference from n"""
    return math.sqrt(np.mean((vals - n)**2))

parsearg = argparse.ArgumentParser(description='Process periodicity trials',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('resfiles', type=str, nargs='+', help='Periodogram results')
parsearg.add_argument('--pprecision', type=int, default=1, help='Percentage precision')
parsearg.add_argument('--mprecision', type=int, default=2, help='Mean/std dev precision')
parsearg.add_argument('--pcomp', type=int, default=3, help='Target period component of file names counting backwards')
parsearg.add_argument('--period', type=float, help='Target period to override file component period')
parsearg.add_argument('--thresh', type=float, default=5.0, help='Percent threshold for accepting result')
parsearg.add_argument('--latex', action='store_true', help='Latex output format')
parsearg.add_argument('--noperc', action='store_true', help='Do not display percent target')
parsearg.add_argument('--noval', action='store_true', help='Do not display value')
parsearg.add_argument('--fcomps', type=str, help='File components to print out numbering backwards')

resargs = vars(parsearg.parse_args())

resfiles = resargs['resfiles']
pprec = resargs['pprecision']
mprec = resargs['mprecision']
period = resargs['period']
pcomp = resargs['pcomp']
thresh = resargs['thresh'] / 100.0
latex = resargs['latex']
noperc = resargs['noperc']
noval = resargs['noval']

pfmt = "%%.%df" % pprec
mfmt = "%%.%df" % mprec

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
    nv = ''
    pm = '$ \\pm $'
else:
    fcs = ' '
    nv = '-'
    pm = '+/-'
    

for rf in resfiles:
    outline = []
    
    rfs = os.path.abspath(rf)
    rfbits =  string.split(rfs, '/')
    if fcomps is not None:
        for p in fcomps:
            try:
                c = rfbits[p]
            except IndexError:
                c = ''
            outline.append(c)
  
    if period is None:
        per = float(rfbits[-pcomp])
    else:
        per = period

    results = np.loadtxt(rf)
    thr = per * thresh
    
    sel = np.abs(results - per) <= thr
    nonsel = ~ sel
    
    okres = results[sel]
    nokres = results[nonsel]
   
    if not noperc:
        outline.append(pfmt % (100.0 * len(okres) / len(results)))
    if not noval:
        if len(okres) == 0:
            outline.append(nv)
            outline.append(nv)
        else:
            s = okres.std()
            if round(s, 2) == 0.0:
                outline.append(mfmt % okres.mean())
            else:
                outline.append((mfmt + '%s' + mfmt) % (okres.mean(), pm, s))
    print string.join(outline, fcs)
