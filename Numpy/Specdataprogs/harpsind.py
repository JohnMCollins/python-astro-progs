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
import scipy.integrate as si
import miscutils
import xmlutil
import specinfo
import specdatactrl
import datarange
import jdate
import datetime
import splittime

def integ_value(range, xvalues, yvalues, yerrs):
    """Calculate intensity as per S-M paper"""
    xv, yv, ye = range.select(xvalues, yvalues, yerrs)
    return (si.trapz(yv, xv), math.sqrt(np.sum(np.square(ye))) * (np.max(xv) - np.min(xv)))

def sum_value(range, xvalues, yvalues, yerrs):
    """Calculate intensity as per S-M paper"""
    xv, yv, ye = range.select(xvalues, yvalues, yerrs)
    return (yv.sum(), math.sqrt(np.sum(np.square(ye))))

SECSPERDAY = 3600.0 * 24.0

parsearg = argparse.ArgumentParser(description='Process HARPS data and generate table of HA inds', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('infofile', type=str, nargs=1, help='Input spectral info file')
parsearg.add_argument('--rangename', type=str, default='smhalpha', help='Range name for H Alpha')
parsearg.add_argument('--contranges', type=str, default='smbc,smrc', help='Range names for continua')
parsearg.add_argument('--outfile', help='Output file name', type=str, required=True)
parsearg.add_argument('--first', type=int, default=0, help='First spectrum number to use')
parsearg.add_argument('--last', type=int, default=10000000, help='Last spectrum number to use')
parsearg.add_argument('--noraw', action='store_true', help='Specify to use normalised values rather than raw')
parsearg.add_argument('--integ', action='store_true', help='Use integration rather than sum')

resargs = vars(parsearg.parse_args())

valrout = sum_value
fetchrout = specdatactrl.SpecDataArray.get_raw_yvalues
rawvals = True

if resargs['integ']:
    valrout = integ_value

if resargs['noraw']:
    fetchrout = specdatactrl.DataArray.get_yvalues
    rawvals = False

infofile = resargs['infofile'][0]
rangename = resargs['rangename']
contr = string.split(resargs['contranges'], ',')
inverting = False
if len(contr) != 2:
    if len(contr) == 1:
        inverting = True
    else:
        print "Expecting 2 continuum ranges"
        sys.exit(9)
outfile = resargs['outfile']
firstspec = resargs['first']
lastspec = resargs['last']

# Now read the info file

if not os.path.isfile(infofile):
    infoflle = miscutils.replacesuffix(infofile, specinfo.SUFFIX)

try:
    sinfo = specinfo.SpecInfo()
    sinfo.loadfile(infofile)
    ctrllist = sinfo.get_ctrlfile()
    rangelist = sinfo.get_rangelist()
    selected_range = rangelist.getrange(rangename)
    cont1 = rangelist.getrange(contr[0])
    if inverting:
        cont1, cont2 = cont1.invert()
    else:
        cont2 = rangelist.getrange(contr[1])
except specinfo.SpecInfoError as e:
    print "Cannot open info file, error was", e.args[0]
    sys.exit(12)
except datarange.DataRangeError as e:
    print "Cannot open range file error was", e.args[0]
    sys.exit(13)

try:
    ctrllist.loadfiles()
except specdatactrl.SpecDataError as e:
    print "Error loading files", e.args[0]
    sys.exit(14)

results = []

for n, spectrum in enumerate(ctrllist.datalist):

    if n < firstspec or n > lastspec:
        continue

    # Get spectral data but skip over ones we've already marked to ignore

    try:
        xvalues = spectrum.get_xvalues()
        yvalues = fetchrout(spectrum)
        yerrs = spectrum.get_yerrors(rawvals=rawvals)

    except specdatactrl.SpecDataError:
        continue

    mha, mhae = valrout(selected_range, xvalues, yvalues, yerrs)
    mrc, mrce = valrout(cont2, xvalues, yvalues, yerrs)
    mbc, mbce = valrout(cont1, xvalues, yvalues, yerrs)
    scont = mbc + mrc
    indval = mha / scont
    ivsq = indval * indval
    inderr = math.sqrt((mhae**2 + ivsq*mrce**2 + ivsq*mbce**2)/(scont * scont))
    #inderr = indval * math.sqrt((mhae/mha)**2 + (mrce**2 + mbce**2)/scont**2)
    #print "mha=",mha,"mhae=",mhae
    #print "mrc=",mrc,"mrce=",mrce
    #print "mbc=",mrc,"mbce=",mbce

    results.append((spectrum.modjdate, spectrum.modbjdate, indval, inderr, 0.0, 0.0, 1.0, 0.0))

np.savetxt(outfile, results)
