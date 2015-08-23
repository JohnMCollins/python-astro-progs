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

resargs = vars(parsearg.parse_args())

perc = resargs['percent']
ewfiles = resargs['ewfiles']
prec = resargs['precision']
fmtseg = "%%#.%dg" % prec
fmt = string.join([ fmtseg ] * 6, ' ')

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
    print fmt % (mew, sew, mps, sps, mpr, spr)

if errors > 0:
    sys.exit(10)
sys.exit(0)