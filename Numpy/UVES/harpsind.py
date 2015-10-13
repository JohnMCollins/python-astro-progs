#! /usr/bin/env python

# Generate table of Jdate / Barydate / EW / Interpolated X-ray values from UVES files / X-ray gradient

import sys
import os
import string
import re
import os.path
import locale
import argparse
import numpy as np
import scipy.integrate as si
import miscutils
import xmlutil
import specinfo
import specdatactrl
import datarange
import jdate
import datetime
import numpy as np
import splittime

def integ_value(range, xvalues, yvalues):
    """Calculate intensity as per S-M paper"""
    xv, yv = range.select(xvalues, yvalues)
    return si.trapz(yv, xv)

SECSPERDAY = 3600.0 * 24.0

parsearg = argparse.ArgumentParser(description='Process HARPS data and generate table of HA inds')
parsearg.add_argument('infofile', type=str, nargs=1, help='Input spectral info file')
parsearg.add_argument('--rangename', type=str, default='smhalpha', help='Range name for H Alpha')
parsearg.add_argument('--contranges', type=str, default='smbc,smrc', help='Range names for continua')
parsearg.add_argument('--outfile', help='Output file name', type=str, required=True)
parsearg.add_argument('--first', type=int, default=0, help='First spectrum number to use')
parsearg.add_argument('--last', type=int, default=10000000, help='Last spectrum number to use')

resargs = vars(parsearg.parse_args())

infofile = resargs['infofile'][0]
rangename = resargs['rangename']
contr = string.split(resargs['contranges'], ',')
if len(contr) != 2:
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
        yvalues = spectrum.get_raw_yvalues()

    except specdatactrl.SpecDataError:
        continue

    mha = integ_value(selected_range, xvalues, yvalues)
    mrc = integ_value(cont2, xvalues, yvalues)
    mbc = integ_value(cont1, xvalues, yvalues)

    results.append((spectrum.modjdate, spectrum.modbjdate, mha / (mbc + mrc), 0.0, 0.0, 0.0, 1.0, 0.0))

np.savetxt(outfile, results)
