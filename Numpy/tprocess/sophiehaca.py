#! /usr/bin/env python

# Generate table of Jdate / Barydate / EW / Interpolated X-ray values from UVES files / X-ray gradient

import sys
import os
import string
import re
import os.path
import locale
import argparse
import math
import numpy as np
import miscutils
import xmlutil
import specinfo
import specdatactrl
import datarange
import jdate
import datetime
import splittime

SECSPERDAY = 3600.0 * 24.0

def sum_value(range, xvalues, yvalues, yerrs):
    """Calculate intensity as per S-M paper"""
    xv, yv, ye = range.select(xvalues, yvalues, yerrs)
    return (yv.sum(), math.sqrt(np.sum(np.square(ye))))

def triang_value(range, xvalues, yvalues, yerrs):
    """Ditto but for triangular ruange"""
    xv, yv, ye = range.select_triang(xvalues, yvalues, yerrs)
    return (yv.sum(), math.sqrt(np.sum(np.square(ye))))

parsearg = argparse.ArgumentParser(description='Process HARPS data and generate logHK', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('--cahinf', type=str, required=True, help='Info file for CaH')
parsearg.add_argument('--cakinf', type=str, required=True, help='Info file for CaK')
parsearg.add_argument('--cahrange', type=str, default='CaH', help='Range names for CaH')
parsearg.add_argument('--cakrange', type=str, default='CaK', help='Range names for CaK')
parsearg.add_argument('--outfile', help='Output file name', type=str, required=True)
parsearg.add_argument('--triangular', action='store_true', help='Specify triangular bandpass')

resargs = vars(parsearg.parse_args())

cahinf = resargs['cahinf']
cakinf = resargs['cakinf']
cahrange = resargs['cahrange']
cakrange = resargs['cakrange']
outfile = resargs['outfile']
if  resargs['triangular']:
    sumrout = triang_value
else:
    sumrout = sum_value

# Now read the info files

if not os.path.isfile(cahinf):
    cahinf = miscutils.replacesuffix(cahinf, specinfo.SUFFIX)
if not os.path.isfile(cakinf):
    cakinf = miscutils.replacesuffix(cakinf, specinfo.SUFFIX)

try:
    cahinfo = specinfo.SpecInfo()
    cahinfo.loadfile(cahinf)
    hctrllist = cahinfo.get_ctrlfile()
    hrangelist = cahinfo.get_rangelist()
    hselected_range = hrangelist.getrange(cahrange)
    cakinfo = specinfo.SpecInfo()
    cakinfo.loadfile(cakinf)
    kctrllist = cakinfo.get_ctrlfile()
    krangelist = cakinfo.get_rangelist()
    kselected_range = krangelist.getrange(cakrange)
except specinfo.SpecInfoError as e:
    print "Cannot open info file, error was", e.args[0]
    sys.exit(12)
except datarange.DataRangeError as e:
    print "Cannot open range file error was", e.args[0]
    sys.exit(13)

try:
    hctrllist.loadfiles()
    kctrllist.loadfiles()
except specdatactrl.SpecDataError as e:
    print "Error loading files", e.args[0]
    sys.exit(14)

results = []

for hspec, kspec in zip(hctrllist.datalist, kctrllist.datalist):
    
    # Get spectral data but skip over ones we've already marked to ignore

    try:
        hxvalues = hspec.get_xvalues()
        hyvalues = hspec.get_yvalues()
        hyerrs = hspec.get_yerrors(rawvals=True)
        kxvalues = kspec.get_xvalues()
        kyvalues = kspec.get_yvalues()
        kyerrs = kspec.get_yerrors(rawvals=True)

    except specdatactrl.SpecDataError:
        continue

    mh, mhe = sumrout(hselected_range, hxvalues, hyvalues, hyerrs)
    mk, mke = sumrout(kselected_range, kxvalues, kyvalues, kyerrs)
    
    lograt = math.log10(mh/mk)
    raterr = math.sqrt((mhe/mh)**2 + (mke/mk)**2)
    results.append((hspec.modjdate, hspec.modbjdate, lograt, raterr, 0.0, 0.0, 1.0, 0.0))

np.savetxt(outfile, results)
