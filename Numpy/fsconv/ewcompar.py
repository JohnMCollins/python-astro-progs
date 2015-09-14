#! /usr/bin/env python

# Process a pile ew results a table giving ew ps pr mean and std

import argparse
import sys
import numpy as np
import string
import jdate
import splittime
import periodarg

def printline(pref1, pref2, ewlist, pslist, prlist, ismed, isperc):
    """Print a line of output with the various prefixes"""
    if ismed:
        mew = np.median(ewlist)
        mps = np.median(pslist)
        mpr = np.median(prlist)
    else:
        mew = np.mean(ewlist)
        mps = np.mean(pslist)
        mpr = np.mean(prlist)
    sew = np.std(ewlist)
    sps = np.std(pslist)
    spr = np.std(prlist)
    if isperc:
        sew *= 100.0 / mew
        sps *= 100.0 / mps
        spr *= 100.0 / mpr
    print pref1 + pref2 + fmt % (mew, sew, mps, sps, mpr, spr)
    
td = np.vectorize(jdate.jdate_to_datetime)
    
parsearg = argparse.ArgumentParser(description='Display EW/PS/PRs mean/std from files')
parsearg.add_argument('ewfiles', type=str, nargs='+', help='EW file(s)')
parsearg.add_argument('--precision', type=int, default=8, help='Precision, default 8')
parsearg.add_argument('--percent', action='store_true', help='Give std as percentage')
parsearg.add_argument('--latex', action='store_true', help='Put in Latex table boundaries')
parsearg.add_argument('--fcomps', type=str, help='Prefix by file name components going backwards thus 1:3')
parsearg.add_argument('--median', action='store_true', help='Show median rather than men')
parsearg.add_argument('--sepdays', type=float, default=0.0, help='Days to do separate rows for')

resargs = vars(parsearg.parse_args())

perc = resargs['percent']
latex = resargs['latex']
ewfiles = resargs['ewfiles']
prec = resargs['precision']
ismed = resargs['median']
sepdays = resargs['sepdays'] * periodarg.SECSPERDAY
fmtseg = "%%.%df" % prec
if latex:
    fcs = ' & '
    sd_all = '\\multicolumn{2}{|c|}{ALL} & '
    if perc:
        fmt = string.join([ fmtseg ] * 6, ' & ') + ' \\\\\\hline'
    else:
        fmt = string.join([ fmtseg + ' $ \\pm $ ' + fmtseg ] * 3, ' & ') + ' \\\\\\hline'
else:
    fmt = string.join([ fmtseg ] * 6, ' ')
    sd_all = 'ALL - '
    fcs = ' '

fcomps = resargs['fcomps']
if fcomps is not None:
    try:
        fcomps = map(lambda x: -int(x), string.split(fcomps, ':'))
    except ValueError:
        sys.stdout = sys.stderr
        print "Cannot understand fcomps arg", fcomps
        sys.exit(20)

errors = 0

for fil in ewfiles:
    try:
        inp = np.loadtxt(fil, unpack=True)
        jdats = inp[0]
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
    pref2 = ' '
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
    
    if sepdays != 0.0:
        ddats = td(jdats)
        tparts = splittime.splittime(sepdays, ddats, ews, pss, prs)
        if len(tparts) > 1:
            for day_dates, day_ews, day_pss, day_prs in tparts:
                fdate = day_dates[0].strftime("%d/%m/%y")
                tdate = day_dates[-1].strftime("%d/%m/%y")
                if len(day_dates) == 1: tdate = "(same)"
                pref2 = string.join([fdate, tdate, ''], fcs)
                printline(pref, pref2, day_ews, day_pss, day_prs, ismed, perc)
        pref2 = sd_all
    
    printline(pref, pref2, ews, pss, prs, ismed, perc)    

if errors > 0:
    sys.exit(10)
sys.exit(0)