#! /usr/bin/env python

# Process a pile ew results a table giving ew ps pr mean and std

import argparse
import sys
import math
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

def appsnr(vec, sig, err):
    """If we are printing errors, append a SNR value to vector, but not if the value is zero"""
    
    global pluse    # Also gives format
    global snrlim
    global great
    if pluse is None: return
    if abs(err) < 1e-12:
        vec.append('-')
    rat = sig / err
    if rat >= snrlim:
        vec.append('%s%g' % (great, snrlim))
    else:
        vec.append(pluse % rat)

def printline(pref1, pref2, ewlist, ewelist, pslist, pselist, prlist, prelist, ismed):
    """Print a line of output with the various prefixes"""
    global prec, fmtseg, noew, nops, nopr, fcs, endl, fudge
    if ismed:
        mew = np.median(ewlist) * fudge
        mps = np.median(pslist)
        mpr = np.median(prlist)
    else:
        mew = np.mean(ewlist) * fudge
        mps = np.mean(pslist)
        mpr = np.mean(prlist)
    sew = np.std(ewlist) * fudge
    sps = np.std(pslist)
    spr = np.std(prlist)
    eew = math.sqrt(np.mean(np.square(ewelist)))
    eps = math.sqrt(np.mean(np.square(pselist)))
    epr = math.sqrt(np.mean(np.square(prelist)))
    
    res = pref1 + pref2
    reslist = []
    if not noew:
        reslist.append(pseg(mew, sew))
        appsnr(reslist, mew, eew)
    if not nops:
        reslist.append(pseg(mps, sps))
        appsnr(reslist, mps, eps)
    if not nopr:
        reslist.append(pseg(mpr, spr))
        appsnr(reslist, mpr, epr)
    print string.strip(res) + ' ' + string.join(reslist, fcs) + endl
    
td = np.vectorize(jdate.jdate_to_datetime)
    
parsearg = argparse.ArgumentParser(description='Display EW/PS/PRs mean/std from files',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('ewfiles', type=str, nargs='+', help='EW file(s)')
parsearg.add_argument('--precision', type=int, default=3, help='Precision, default 8')
parsearg.add_argument('--latex', action='store_true', help='Put in Latex table boundaries')
parsearg.add_argument('--noendl', action='store_true', help='Dont put hlines in in latex mode')
parsearg.add_argument('--fcomps', type=str, help='Prefix by file name components going backwards thus 1:3')
parsearg.add_argument('--median', action='store_true', help='Show median rather than men')
parsearg.add_argument('--sepdays', type=float, default=0.0, help='Days to do separate rows for')
parsearg.add_argument('--noew', action='store_true', help='Omit EW from results')
parsearg.add_argument('--nops', action='store_false', help='Omit PS from results')
parsearg.add_argument('--nopr', action='store_false', help='Omit PR from results')
parsearg.add_argument('--fudge', type=float, default=1.0, help='Fudge factor for EWs')
parsearg.add_argument('--pluse', type=int, help='Insert column for (RMS) SNR giving digits prec')
parsearg.add_argument('--snrlim', type=float, default=1e6, help='Limit for SNR display')

resargs = vars(parsearg.parse_args())

noew = resargs['noew']
nops = resargs['nops']
nopr = resargs['nopr']
latex = resargs['latex']
ewfiles = resargs['ewfiles']
prec = resargs['precision']
fudge = resargs['fudge']
pluse = resargs['pluse']
snrlim = resargs['snrlim']
ismed = resargs['median']
sepdays = resargs['sepdays'] * periodarg.SECSPERDAY
fmtseg = "%%.%df" % prec
if latex:
    great = '$>$'
    fcs = ' & '
    pm = ' $ \\pm $ '
    sd_all = '\\multicolumn{2}{|c|}{ALL} & '
    nopm = ''
    endl = ' \\\\\\hline'
    if resargs['noendl']:
        endl = fcs
else:
    great = '>'
    sd_all = 'ALL - '
    fcs = ' '
    pm = ' '
    nopm = '-'
    endl = ''

if pluse is not None:
    pluse = "%%.%df" % abs(pluse)

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
        ewes = inp[3]
        pss = inp[4]
        pses = inp[5]
        prs = inp[6]
        pres = inp[7]
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
        tparts = splittime.splittime(sepdays, ddats, ews, ewes, pss, pses, prs, pres)
        if len(tparts) > 1:
            for day_dates, day_ews, day_ewes, day_pss, day_pses, day_prs, day_pres in tparts:
                fdat = day_dates[0]
                tdat = day_dates[-1]
                fdate = fdat.strftime("%d/%m/%Y")
                tdate = tdat.strftime("%d/%m/%Y")
                if fdat.date() == tdat.date(): tdate = "(same)"
                pref2 = string.join([fdate, tdate, str(len(day_dates)), ''], fcs)
                printline(pref, pref2, day_ews, day_ewes, day_pss, day_pses, day_prs, day_pres, ismed)
        pref2 = sd_all + str(len(ews)) + fcs
    
    printline(pref, pref2, ews, ewes, pss, pses, prs, pres, ismed)    

if errors > 0:
    sys.exit(10)
sys.exit(0)