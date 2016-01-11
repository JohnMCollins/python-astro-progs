#! /usr/bin/env python

import sys
import os
import os.path
import string
import locale
import argparse
import numpy as np
import matplotlib.pyplot as plt
import miscutils
import specdatactrl
import datarange
import specinfo

C = 299792.458

parsearg = argparse.ArgumentParser(description='Fit polynomial to given region of spectra', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('infofile', type=str, help='Specinfo file', nargs=1)
parsearg.add_argument('--rangename', type=str, default='halpha', help='Range name to fit')
parsearg.add_argument('--outfile', help='Output file name', type=str, required=True)
parsearg.add_argument('--first', type=int, default=0, help='First spectrum number to use')
parsearg.add_argument('--last', type=int, default=10000000, help='Last spectrum number to use')
parsearg.add_argument('--degree', type=int, default=10, help='Order of polynomial to fit, default 10')
parsearg.add_argument('--offset', type=float, help='centre of wavelength offset or just centre of range')
parsearg.add_argument('--points', type=int, default=150, help='Number of points either side of centre')

resargs = vars(parsearg.parse_args())

infofile = resargs['infofile'][0]
rangename = resargs['rangename']
outfile = resargs['outfile']
firstspec = resargs['first']
lastspec = resargs['last']
degree = resargs['degree']
offset = resargs['offset']
points = resargs['points']

if not os.path.isfile(infofile):
    infofile = miscutils.replacesuffix(infofile, specinfo.SUFFIX)

try:
    inf = specinfo.SpecInfo()
    inf.loadfile(infofile)
    ctrllist = inf.get_ctrlfile()
    rangl = inf.get_rangelist()
except specinfo.SpecInfoError as e:
    sys.stdout = sys.stderr
    print "Cannot load info file", infofile
    print "Error was:", e.args[0]
    sys.exit(100)

try:
    ctrllist.loadfiles()
except specdatactrl.SpecDataError as e:
    sys.stdout = sys.stderr
    print "Problem loading files via", infofile
    print "Error was:", e.args[0]
    sys.exit(101)

try:
    selected_range = rangl.getrange(rangename)
except datarange.DataRangeError as e:
    print "Cannot select range", rangename, "error was", e.args[0]
    sys.exit(13)

    
# Process data according to day

xvalues = np.array([])
yvalues = np.array([])

for n, spectrum in enumerate(ctrllist.datalist):
    
    if n < firstspec or n > lastspec:
        continue

    # Get spectral data but skip over ones we've already marked to ignore
    try:
        xv = spectrum.get_xvalues(False)
        yv = spectrum.get_yvalues(False)
    except specdatactrl.SpecDataError:
        continue
    
    xv, yv = selected_range.select(xv, yv)
    xvalues = np.concatenate((xvalues, xv))
    yvalues = np.concatenate((yvalues, yv))

if offset is None:
    offset = (selected_range.lower + selected_range.upper) / 2.0

xvalues -= offset

pcs = np.polyfit(xvalues, yvalues, degree)

minx = np.min(xvalues)
maxx = np.max(xvalues)

xr = np.linspace(minx, maxx, 2*points+1)
yr = np.polyval(pcs, xr)

yr /= yr[0]

xvs = xr * C / offset

np.savetxt(outfile, np.array([xvs, yr]).transpose(), fmt='%#.6g')
plt.plot(xvs, yr)
plt.show()

#np.savetxt(outfile, results)

sys.exit(0)
