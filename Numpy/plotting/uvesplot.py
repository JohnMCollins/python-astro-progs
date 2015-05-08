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
import datetime
import numpy as np
import matplotlib.pyplot as plt

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
baycent = resargs['baycentric']
xraylevels = resargs['xraylevel']

if len(xrayfiles) != 3:
    print "Expecting 3 X ray files"
    sys.exit(10)

sort(xrayfiles)

# Kick off by reading in X-ray data

xraydata = []
for xrf in xrayfiles:
    try:
        xray_amp, xray_err, xray_time = np.loadtxt(xrayfile, unpack=True)
        xray_time %= SECSPERDAY
        interpfn = si.interp1d(xray_time, xray_amp, kind='cubic', bounds_error=False, fill_value=deflevel, assume_sorted=True)
    except IOError as e:
        print "Cannoot open", xrf, "Error was", e.args[1]
        sys.exit(11)
    xraydata.append((xray_time, xray_amp))

# Now read the control file

try:
    ctrllist = specdatactrl.Load_specctrl(ctrlfile)
except specdatactrl.SpecDataError as e:
    print "Cannot open control file, error was", e.args[0]
    sys.exit(12)

# Open the range file

try:
    rangelist = datarange.load_ranges(rangefile)
    selected_range = rangelist.get_range(rangename)
except datarange.DataRangeError as e:
    print "Cannot open range file error was", e.args[0]
    sys.exit(13)

# Now stuff for each day

daydata = []

