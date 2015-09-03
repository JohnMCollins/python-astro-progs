#! /usr/bin/env python

# Process a pile ew results a table giving ew ps pr mean and std

import argparse
import sys
import numpy as np
import string

parsearg = argparse.ArgumentParser(description='Display EW/PS/PRs mean/std from files')
parsearg.add_argument('ewfiles', type=str, nargs='+', help='EW file(s)')
parsearg.add_argument('--precision', type=int, default=8, help='Precision, default 8')
parsearg.add_argument('--percent', action='store_true', help='Give std as percentage')
parsearg.add_argument('--latex', action='store_true', help='Put in Latex table boundaries')
parsearg.add_argument('--fcomps', type=str, help='Prefix by file name components going backwards thus 1:3')

resargs = vars(parsearg.parse_args())

perc = resargs['percent']
latex = resargs['latex']
ewfiles = resargs['ewfiles']
prec = resargs['precision']
fmtseg = "%%.%df" % prec
if latex:
    if perc:
        fmt = string.join([ fmtseg ] * 6, ' & ') + ' \\\\\\hline'
    else:
        fmt = string.join([ fmtseg + ' $ \\pm $ ' + fmtseg ] * 3, ' & ') + ' \\\\\\hline'
else:
    fmt = string.join([ fmtseg ] * 6, ' ')

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
    else:
        fcs = ' '

errors = 0

for fil in ewfiles:
    try:
        inp = np.loadtxt(fil, unpack=True)
        ews = inp[2]
        pss = inp[4]
        prs = inp[6]
    except IOError as e:
        sys.stdout = sys.stderr
        print "Cannot read", fil, "-", e.args[1]
        sys.stdout = sys.__stdout__
        errors += 1
        continue
    
    pref = ''
    if fcomps is not None:
        pref = []
        ewfbits = string.split(fil, '/')
        for p in fcomps:
            try:
                c = ewfbits[p]
            except IndexError:
                c = ''
            pref.append(c)
        pref.append('')
        pref = string.join(pref, fcs)
        
    mew = ews.mean()
    mps = pss.mean()
    mpr = prs.mean()
    sew = ews.std()
    sps = pss.std()
    spr = prs.std()
    if perc:
        sew *= 100.0 / mew
        sps *= 100.0 / mps
        spr *= 100.0 / mpr
    print pref + fmt % (mew, sew, mps, sps, mpr, spr)

if errors > 0:
    sys.exit(10)
sys.exit(0)