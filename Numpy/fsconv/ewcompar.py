#! /usr/bin/env python

# Process a pile ew results a table giving ew ps pr mean and std

import argparse
import sys
import numpy as np
import string
import jdate
import splittime
import periodarg

def pseg(m, s):
    """Print a value with std dev"""
    global prec, fmtseg, pm, nopm
    if round(s, prec) == 0.0:
        return fmtseg % m + nopm
    return fmtseg % m + pm + fmtseg % s

def printline(pref1, pref2, ewlist, pslist, prlist, ismed, isperc):
    """Print a line of output with the various prefixes"""
    global prec, fmtseg, noew, nops, nopr, fcs, endl
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
    
    res = pref1 + pref2
    reslist = []
    
    if isperc:
        sew *= 100.0 / mew
        sps *= 100.0 / mps
        spr *= 100.0 / mpr
        if not noew:
            reslist.append(fmtseg % mew)
            reslist.append(fmtseg % sew)
        if not nops:
            reslist.append(fmtseg % mps)
            reslist.append(fmtseg % sps)
        if not nopr:
            reslist.append(fmtseg % mpr)
            reslist.append(fmtseg % spr)
    else:
        if not noew: reslist.append(pseg(mew, sew))
        if not nops: reslist.append(pseg(mps, sps))
        if not nopr: reslist.append(pseg(mpr, spr))
    print string.strip(res) + ' ' + string.join(reslist, fcs) + endl
    
td = np.vectorize(jdate.jdate_to_datetime)
    
parsearg = argparse.ArgumentParser(description='Display EW/PS/PRs mean/std from files')
parsearg.add_argument('ewfiles', type=str, nargs='+', help='EW file(s)')
parsearg.add_argument('--precision', type=int, default=8, help='Precision, default 8')
parsearg.add_argument('--percent', action='store_true', help='Give std as percentage')
parsearg.add_argument('--latex', action='store_true', help='Put in Latex table boundaries')
parsearg.add_argument('--noendl', action='store_true', help='Dont put hlines in in latex mode')
parsearg.add_argument('--fcomps', type=str, help='Prefix by file name components going backwards thus 1:3')
parsearg.add_argument('--median', action='store_true', help='Show median rather than men')
parsearg.add_argument('--sepdays', type=float, default=0.0, help='Days to do separate rows for')
parsearg.add_argument('--noew', action='store_true', help='Omit EW from results')
parsearg.add_argument('--nops', action='store_true', help='Omit PS from results')
parsearg.add_argument('--nopr', action='store_true', help='Omit PR from results')

resargs = vars(parsearg.parse_args())

noew = resargs['noew']
nops = resargs['nops']
nopr = resargs['nopr']
perc = resargs['percent']
latex = resargs['latex']
ewfiles = resargs['ewfiles']
prec = resargs['precision']
ismed = resargs['median']
sepdays = resargs['sepdays'] * periodarg.SECSPERDAY
fmtseg = "%%.%df" % prec
if latex:
    fcs = ' & '
    pm = ' $ \\pm $ '
    sd_all = '\\multicolumn{2}{|c|}{ALL} & '
    nopm = ''
    endl = ' \\\\\\hline'
    if resargs['noendl']:
        endl = fcs
else:
    sd_all = 'ALL - '
    fcs = ' '
    pm = ' '
    nopm = '-'
    endl = ''

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
                fdat = day_dates[0]
                tdat = day_dates[-1]
                fdate = fdat.strftime("%d/%m/%y")
                tdate = tdat.strftime("%d/%m/%y")
                if fdat.date() == tdat.date(): tdate = "(same)"
                pref2 = string.join([fdate, tdate, str(len(day_dates)), ''], fcs)
                printline(pref, pref2, day_ews, day_pss, day_prs, ismed, perc)
        pref2 = sd_all + str(len(ews)) + fcs
    
    printline(pref, pref2, ews, pss, prs, ismed, perc)    

if errors > 0:
    sys.exit(10)
sys.exit(0)