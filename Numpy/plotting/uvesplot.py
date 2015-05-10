#! /usr/bin/env python

# Apply X-ray file to UVES data to mark

import sys
import os
import re
import os.path
import locale
import argparse
import numpy as np
import scipy.interpolate as si
import miscutils
import xmlutil
import specdatactrl
import datarange
import jdate
import meanval
import datetime
import numpy as np
import matplotlib.pyplot as plt

SECSPERDAY = 3600.0 * 24.0

parsearg = argparse.ArgumentParser(description='Process UVES data and show plots of effectively suppressing where X-ray levels are high')
parsearg.add_argument('--ctrl', type=str, help='Input control file', required=True)
parsearg.add_argument('--rangefile', type=str, help='Range file', required=True)
parsearg.add_argument('--rangename', type=str, default='halpha', help='Range name to calculate equivalent widths')
parsearg.add_argument('--xrayfile', type=str, nargs='*', help='Xray data files')
parsearg.add_argument('--width', help="Width of plot", type=float, default=8)
parsearg.add_argument('--height', help="Height of plot", type=float, default=8)
parsearg.add_argument('--hwidth', help="Width of histogram", type=float, default=8)
parsearg.add_argument('--hheight', help="Height of histogram", type=float, default=8)
parsearg.add_argument('--deflevel', type=float, default=0.0, help='Default level of X-ray for points outside time range')
parsearg.add_argument('--barycentric', action='store_true', help='Use barycentric date/time now obs date/time')
parsearg.add_argument('xraylevel', type=float, nargs='+', help='Level of xray activity at which we discount data')

resargs = vars(parsearg.parse_args())

ctrlfile = resargs['ctrl']
rangefile = resargs['rangefile']
rangename = resargs['rangename']
xrayfiles = resargs['xrayfile']
width = resargs['width']
height = resargs['height']
hwidth = resargs['hwidth']
hheight = resargs['hheight']
deflevel = resargs['deflevel']
baycent = resargs['barycentric']
xraylevels = resargs['xraylevel']

if len(xrayfiles) != 3:
    print "Expecting 3 X ray files"
    sys.exit(10)

xrayfiles.sort()

# Kick off by reading in X-ray data

xraydata = []
for xrf in xrayfiles:
    try:
        xray_amp, xray_err, xray_time = np.loadtxt(xrf, unpack=True)
        xray_time %= SECSPERDAY
        interpfn = si.interp1d(xray_time, xray_amp, kind='cubic', bounds_error=False, fill_value=deflevel, assume_sorted=True)
    except IOError as e:
        print "Cannoot open", xrf, "Error was", e.args[1]
        sys.exit(11)
    xraydata.append((interpfn, xray_time, xray_amp))

# Now read the control file

try:
    ctrllist = specdatactrl.Load_specctrl(ctrlfile)
except specdatactrl.SpecDataError as e:
    print "Cannot open control file, error was", e.args[0]
    sys.exit(12)

# Open the range file

try:
    rangelist = datarange.load_ranges(rangefile)
    selected_range = rangelist.getrange(rangename)
except datarange.DataRangeError as e:
    print "Cannot open range file error was", e.args[0]
    sys.exit(13)

try:
    ctrllist.loadfiles()
except specdatactrl.SpecDataError as e:
    print "Error loading files", e.args[0]
    sys.exit(14)

# Now stuff for each day

daydata = []
cday = []

# Initialise date to something way past the first date

lastdate = ctrllist.datalist[0].modjdate + 10000

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
    
    if spectrum.modjdate - lastdate >= 1.0:
        
        daydata.append(cday)
        cday = []
    
    lastdate = spectrum.modjdate
    cday.append((spectrum.modjdate, spectrum.modbjdate, ew))

if len(cday) != 0:
    daydata.append(cday)

# Plot for each day

for cday in daydata:
    
    xrd = xraydata.pop(0)
    interpfn, xray_time, xray_amp = xrd
    
    plt.figure()
    plt.subplots_adjust(hspace = 0)
    ax1 = plt.subplot(2,1,1)
    ax1.get_xaxis().get_major_formatter().set_useOffset(False)
    
    add = np.array(cday)
    add = add.transpose()
    times = (add[0] % SECSPERDAY - SECSPERDAY/2.0) / 3600.0
    plt.plot(times, add[2])
    
    plt.subplot(2,1,2,sharex=ax1)
    
    times = ((xray_time / SECSPERDAY) % 1.0) * 24.0
    print times
    
    #plt.plot(times, xray_amp)

plt.show()
