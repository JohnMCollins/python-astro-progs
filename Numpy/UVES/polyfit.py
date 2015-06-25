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
import scipy.interpolate as si
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
import matplotlib.pyplot as plt

parsearg = argparse.ArgumentParser(description='Process UVES data and generate table of EWs')
parsearg.add_argument('--infofile', type=str, help='Input spectral info file', required=True)
parsearg.add_argument('--rangename', type=str, default='halpha', help='Range name to calculate equivalent widths')
parsearg.add_argument('--outprefix', help='Output file name prefix', type=str, required=True)
parsearg.add_argument('--degree', type=int, default=10, help='Degree of polynomial')

resargs = vars(parsearg.parse_args())

infofile = resargs['infofile']
rangename = resargs['rangename']
outfile = resargs['outprefix']
deg = resargs['degree']

# Now read the info file

if not os.path.isfile(infofile):
    infoflle = miscutils.replacesuffix(infofile, specinfo.SUFFIX)

try:
    sinfo = specinfo.SpecInfo()
    sinfo.loadfile(infofile)
    ctrllist = sinfo.get_ctrlfile()
    rangelist = sinfo.get_rangelist()
    selected_range = rangelist.getrange(rangename)
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

for spectrum in ctrllist.datalist:

    # Get spectral data but skip over ones we've already marked to ignore

    try:
        xvalues = spectrum.get_xvalues(False)
        yvalues = spectrum.get_yvalues(False)

    except specdatactrl.SpecDataError:
        continue

    selxvals, selyvals = selected_range.select(xvalues, yvalues)
    plt.figure()
    plt.plot(selxvals, selyvals)

plt.show()

    