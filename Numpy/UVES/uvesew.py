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

SECSPERDAY = 3600.0 * 24.0

parsearg = argparse.ArgumentParser(description='Process UVES data and generate table of EWs')
parsearg.add_argument('--infofile', type=str, help='Input spectral info file', required=True)
parsearg.add_argument('--rangename', type=str, default='halpha', help='Range name to calculate equivalent widths')
parsearg.add_argument('--peakranges', type=str, default='integ1,integ2', help='Range names for subpeaks')
parsearg.add_argument('--xrayoffset', type=float, default=0.0, help='Offset to X-ray times')
parsearg.add_argument('--outfile', help='Output file name', type=str, required=True)
parsearg.add_argument('xrayfiles', type=str, nargs='+', help='X-ray data files')

resargs = vars(parsearg.parse_args())

infofile = resargs['infofile']
rangename = resargs['rangename']
peakranges = string.split(resargs['peakranges'], ',')
if len(peakranges) != 2:
    print "Expecting 2 peak ranges"
    sys.exit(9)
xrayfiles = resargs['xrayfiles']
xrayoffset = resargs['xrayoffset']
outfile = resargs['outfile']


if len(xrayfiles) != 3:
    print "Expecting 3 X ray files"
    sys.exit(10)

xrayfiles.sort()

# Kick off by reading in X-ray data also work out gradient and get interpfn

xraydata = []
maxamp = 0
mingrad = 1e20
maxgrad = -1e20

for daynum, xrf in enumerate(xrayfiles):
    try:
        xray_amp, xray_err, xray_time = np.loadtxt(xrf, unpack=True)

        xray_time += xrayoffset
        xray_time /= SECSPERDAY
        xray_time += 50814.0            # 1/1/1998 for whatever reason

        xray_timediff = np.mean(np.diff(xray_time))
        xray_gradient = np.gradient(xray_amp, xray_timediff)

        maxamp = max(maxamp, np.max(xray_amp))
        mingrad = min(mingrad, np.min(xray_gradient))
        maxgrad = max(maxgrad, np.max(xray_gradient))

        interpfn = si.interp1d(xray_time, xray_amp, kind='cubic', bounds_error=False, fill_value=1e50, assume_sorted=True)
        ginterpfn = si.interp1d(xray_time, xray_gradient, kind='cubic', bounds_error=False, fill_value=1e50, assume_sorted=True)

    except IOError as e:
        print "Cannoot open", xrf, "Error was", e.args[1]
        sys.exit(11)

    xraydata.append((interpfn, ginterpfn, xray_time, xray_amp, xray_gradient))

# Now read the info file

if not os.path.isfile(infofile):
    infoflle = miscutils.replacesuffix(infofile, specinfo.SUFFIX)

try:
    sinfo = specinfo.SpecInfo()
    sinfo.loadfile(infofile)
    ctrllist = sinfo.get_ctrlfile()
    rangelist = sinfo.get_rangelist()
    selected_range = rangelist.getrange(rangename)
    integ1 = rangelist.getrange(peakranges[0])
    integ2 = rangelist.getrange(peakranges[1])
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

# Process data according to day

results = []
lastdate = 0
minew = 1e6
maxew = -1e6

for spectrum in ctrllist.datalist:

    # Get spectral data but skip over ones we've already marked to ignore

    try:
        xvalues = spectrum.get_xvalues(False)
        yvalues = spectrum.get_yvalues(False)

    except specdatactrl.SpecDataError:
        continue

    # Calculate equivalent width using meanval calc

    har, hir = meanval.mean_value(selected_range, xvalues, yvalues)
    ew = (hir - har) / har

    minew = min(minew, ew)
    maxew = max(maxew, ew)

    peak1w, peak1s = meanval.mean_value(integ1, xvalues, yvalues)
    peak2w, peak2s = meanval.mean_value(integ2, xvalues, yvalues)

    pr = (peak2s * peak1w) / (peak1s * peak2w)

    # Select next X-ray file if we're on next day

    if spectrum.modjdate - lastdate >= 1.0:
        interpfn, ginterpfn, xray_time, xray_amp, xray_gradient = xraydata.pop(0)
    lastdate = spectrum.modjdate

    results.append((spectrum.modjdate, spectrum.modbjdate, ew, pr, interpfn(lastdate), ginterpfn(lastdate)))

np.savetxt(outfile, results)
