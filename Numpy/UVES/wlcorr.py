#! /usr/bin/env python

# Correlate wavelength values

import sys
import os
import string
import re
import os.path
import locale
import argparse
import numpy as np
import scipy.interpolate as si
import scipy.signal as ss
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
import argmaxmin
import matplotlib.pyplot as plt

parsearg = argparse.ArgumentParser(description='Correlate wavelengths')
parsearg.add_argument('--infofile', type=str, help='Input spectral info file', required=True)
parsearg.add_argument('--rangename', type=str, default='halpha', help='Range name to calculate equivalent widths')
parsearg.add_argument('--specnum', type=int, default=0, help='Spectrum number as base')
parsearg.add_argument('--expandbase', type=float, default=0.1, help='Amount to expand base range for correlation')

resargs = vars(parsearg.parse_args())

infofile = resargs['infofile']
rangename = resargs['rangename']
specnum = resargs['specnum']
expansion = resargs['expandbase']

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

try:
    basespec = ctrllist.datalist[0]
    basex = basespec.get_xvalues(False)
    basey = basespec.get_yvalues(False)
    basex, basey = selected_range.select(basex, basey, expansion)
except specdatactrl.SpecDataError as e:
    print "Error selecting base spectrum", e.args[0]
    sys.exit(15)

basefrom, baseto = selected_range.argselect(basex)
meany = np.mean(basey)

for snum, spectrum in enumerate(ctrllist.datalist):

    # Get spectral data but skip over ones we've already marked to ignore
    
    try:
        xvalues = spectrum.get_xvalues(False)
        yvalues = spectrum.get_yvalues(False)

    except specdatactrl.SpecDataError:
        continue

    selx, sely = selected_range.select(xvalues,  yvalues)
    
    corr = ss.correlate(basey-meany, sely-meany, 'same')
    corrmax = argmaxmin.maxmaxes(corr,corr)
    print "Spectrum", snum, "offset", corrmax[0], "diff", corrmax[0]-basefrom


    