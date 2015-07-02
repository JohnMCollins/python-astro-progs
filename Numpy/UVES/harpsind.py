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
import meanval
import datetime
import numpy as np
import splittime

SECSPERDAY = 3600.0 * 24.0

parsearg = argparse.ArgumentParser(description='Process HARPS data and generate table of HA inds')
parsearg.add_argument('infofile', type=str, nargs=1, help='Input spectral info file')
parsearg.add_argument('--rangename', type=str, default='smhalpha', help='Range name for H Alpha')
parsearg.add_argument('--contranges', type=str, default='smbc,smrc', help='Range names for continua')
parsearg.add_argument('--outfile', help='Output file name', type=str, required=True)

resargs = vars(parsearg.parse_args())

infofile = resargs['infofile'][0]
rangename = resargs['rangename']
contr = string.split(resargs['contranges'], ',')
if len(contr) != 2:
    print "Expecting 2 continuum ranges"
    sys.exit(9)
outfile = resargs['outfile']

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

for spectrum in ctrllist.datalist:

    # Get spectral data but skip over ones we've already marked to ignore

    try:
        xvalues = spectrum.get_xvalues(False)
        yvalues = spectrum.get_yvalues(False)

    except specdatactrl.SpecDataError:
        continue

    mw, mha = meanval.mean_value(selected_range, xvalues, yvalues)
    mw, mrc = meanval.mean_value(cont2, xvalues, yvalues)
    mw, mbc = meanval.mean_value(cont1, xvalues, yvalues)
    
    results.append((spectrum.modjdate, spectrum.modbjdate, mha / (mbc + mrc), 0.0, 0.0, 0.0, 1.0, 0.0))

np.savetxt(outfile, results)
