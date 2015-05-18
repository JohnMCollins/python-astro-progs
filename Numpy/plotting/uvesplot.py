#! /usr/bin/env python

# Apply X-ray file to UVES data to mark

import sys
import os
import string
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
from matplotlib import dates

SECSPERDAY = 3600.0 * 24.0

parsearg = argparse.ArgumentParser(description='Process UVES data and show plots of effectively suppressing where X-ray levels are high')
parsearg.add_argument('--ctrl', type=str, help='Input control file', required=True)
parsearg.add_argument('--rangefile', type=str, help='Range file')
parsearg.add_argument('--rangename', type=str, default='halpha', help='Range name to calculate equivalent widths')
parsearg.add_argument('--xrayfile', type=str, nargs='*', help='Xray data files')
parsearg.add_argument('--xrayoffset', type=float, default=0.0, help='Offset to X-ray times')
parsearg.add_argument('--width', help="Width of plot", type=float, default=8)
parsearg.add_argument('--height', help="Height of plot", type=float, default=8)
parsearg.add_argument('--hwidth', help="Width of histogram", type=float, default=8)
parsearg.add_argument('--hheight', help="Height of histogram", type=float, default=8)
parsearg.add_argument('--bins', help='Histogram bins', type=int, default=20)
parsearg.add_argument('--colours', help='Colours for plot', type=str, default='blue,green,red,black,purple,orange')
parsearg.add_argument('--deflevel', type=float, default=0.0, help='Default level of X-ray for points outside time range')
parsearg.add_argument('--barycentric', action='store_true', help='Use barycentric date/time now obs date/time')
parsearg.add_argument('--onehist', action='store_true', help='Plot on one histogram')
parsearg.add_argument('xraylevel', type=float, nargs='+', help='Level of xray activity at which we discount data')

resargs = vars(parsearg.parse_args())

ctrlfile = resargs['ctrl']
rangefile = resargs['rangefile']
if rangefile is None:
    rangefile = miscutils.replacesuffix(ctrlfile, '.spcr', '.sac')
rangename = resargs['rangename']
xrayfiles = resargs['xrayfile']
width = resargs['width']
height = resargs['height']
hwidth = resargs['hwidth']
hheight = resargs['hheight']
bins = resargs['bins']
deflevel = resargs['deflevel']
baycent = resargs['barycentric']
xraylevels = resargs['xraylevel']
colours = string.split(resargs['colours'], ',')

# Get every combination of min and max levels

minxrays = [-xrl for xrl in xraylevels if xrl<0]
maxxrays = [xrl for xrl in xraylevels if xrl>0]

if len(minxrays) == 0:
    if len(maxxrays) == 0:
        xraylevels = [(0,0)]
    else:
        xraylevels = [(0,xrl) for xrl in maxxrays]
        xraylevels.insert(0, (0.0,0.0))
elif len(maxxrays) == 0:
    xraylevels = [(xrl,0) for xrl in minxrays]
    xraylevels.insert(0, (0.0,0.0))
else:
    if not 0.0 in maxxrays: maxxrays.insert(0,0.0)
    if not 0.0 in minxrays: minxrays.insert(0,0.0)
    xraylevels = [(mn,mx) for mn in minxrays for mx in maxxrays]

nlevs = len(xraylevels)

# Make sure there are enough to cover all the xray levels + 1

while nlevs >= len(colours):
    colours = colours * 2

if len(xrayfiles) != 3:
    print "Expecting 3 X ray files"
    sys.exit(10)

xrayfiles.sort()

# Kick off by reading in X-ray data

xraydata = []
maxamp = 0
for xrf in xrayfiles:
    try:
        xray_amp, xray_err, xray_time = np.loadtxt(xrf, unpack=True)
        maxamp = max(maxamp, np.max(xray_amp))
        xray_time /= SECSPERDAY
        xray_time += 50814.0            # 1/1/1998 for whatever reason
        interpfn = si.interp1d(xray_time, xray_amp, kind='cubic', bounds_error=False, fill_value=deflevel, assume_sorted=True)
    except IOError as e:
        print "Cannoot open", xrf, "Error was", e.args[1]
        sys.exit(11)
    xraydata.append((interpfn, xray_time, xray_amp))

hfmt = dates.DateFormatter('%H:%M')

fig = plt.figure(figsize=(width, height))
fig.canvas.set_window_title("Xray values all to same scale")
ln = 1
commonax = None
plt.subplots_adjust(hspace = 0)
for xrd in xraydata:
    ax1 = plt.subplot(3, 1, ln, sharex=commonax)
    if commonax is None: commonax=ax1
    ifn, xray_time, xray_amp = xrd
    xray_dates = np.array([jdate.jdate_to_datetime(d - ln*2 + 2) for d in xray_time])
    plt.ylim(0, maxamp)
    ax1.xaxis.set_major_formatter(hfmt)
    fig.autofmt_xdate()
    plt.plot(xray_dates, xray_amp, color='black')
    plt.legend(["Day %d" % ln])
    ln += 1

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
    
    if spectrum.modjdate - lastdate >= 1.0:
        
        daydata.append(cday)
        cday = []
    
    lastdate = spectrum.modjdate
    cday.append((spectrum.modjdate, spectrum.modbjdate, ew))

if len(cday) != 0:
    daydata.append(cday)

# Plot for each day

hfmt = dates.DateFormatter('%H:%M')

ewlevs = []
for i in range(0, nlevs):
    ewlevs.append(np.empty(0,))

for cday in daydata:
    
    xrd = xraydata.pop(0)
    interpfn, xray_time, xray_amp = xrd
    
    fig = plt.figure(figsize=(width,height))
    
    plt.subplots_adjust(hspace = 0)
    
    add = np.array(cday)
    day_jdates, day_bjdates, day_ews = add.transpose()
    timesp = np.array([jdate.jdate_to_datetime(d) for d in day_jdates])
    day_xraylev = interpfn(day_jdates)
    plt.xlim(timesp[0], timesp[-1])
    fig.canvas.set_window_title(timesp[0].strftime("For %d %b %Y"))
    
    ax1 = None
    
    for ln, xrl in enumerate(xraylevels):
        pax = plt.subplot(1+nlevs,1,1+ln, sharex=ax1)
        plt.ylim(minew, maxew)
        if ax1 is None: ax1=pax
        minxr, maxxr = xrl
        if minxr <= 0.0:
            if maxxr <= 0.0:
                leg = "No X-ray"
                plot_ews = day_ews
                plot_times = timesp
            else:
                selection = day_xraylev < maxxr
                plot_ews = day_ews[selection]
                plot_times = timesp[selection]
                leg = "X-ray < %.3g" % maxxr
        elif maxxr <= 0.0:
            selection = day_xraylev > minxr
            plot_ews = day_ews[selection]
            plot_times = timesp[selection]
            leg = "X-ray > %.3g" % minxr
        else:
            selection = (day_xraylev > minxr) & (day_xraylev < maxxr)
            plot_ews = day_ews[selection]
            plot_times = timesp[selection]
            leg = "%.3g > X-ray > %.3g" % (maxxr, minxr)
        
        plt.plot(timesp, day_ews,color=colours[ln])
        plt.legend([leg]) 
        ewlevs[ln] = np.append(ewlevs[ln], plot_ews)
  
    ax2 = plt.subplot(1+nlevs,1,1+nlevs,sharex=ax1)
    
    times = [jdate.jdate_to_datetime(d) for d in xray_time]
    
    plt.plot(times, xray_amp)
    for ln, xrl in enumerate(xraylevels):
        minxr, maxxr = xrl
        if minxr > 0.0: plt.axhline(minxr, color=colours[ln])
        if maxxr > 0.0: plt.axhline(maxxr, color=colours[ln])
    plt.legend(["X-ray"])
    plt.xlim(timesp[0], timesp[-1])
    ax2.xaxis.set_major_formatter(hfmt)
    plt.gcf().autofmt_xdate()

fig = plt.figure(figsize=(hwidth, hheight))
fig.canvas.set_window_title("Equivalent widths (all days)")

histews = []
histlegs = []

for ln, xrl in enumerate(xraylevels):
    minxr, maxxr = xrl
    histews.append(ewlevs[ln])
    if minxr <= 0.0:
        if maxxr <= 0.0:
            leg = "No X-ray"
        else:
            leg = "X-ray < %.3g" % maxxr
    elif maxxr <= 0.0:
        leg = "X-ray > %.3g" % minxr
    else:
        leg = "%.3g > X-ray > %.3g" % (maxxr, minxr)
    histlegs.append(leg)

if resargs['onehist']:
    plt.hist(histews)
    plt.legend(histlegs)
else:
    plt.subplots_adjust(hspace = 0)
    ax1 = None
    for ln, xrl in enumerate(xraylevels):
        ews = histews[ln]
        ax = plt.subplot(1+nlevs, 1, 2+ln, sharex=ax1)
        if ax1 is None:
            miny, maxy = ax.get_ylim()
            ax1 = ax
        else:
            plt.ylim(0, maxy)
        plt.hist(ews, bins=bins, color=colours[ln])
        plt.legend(histlegs[ln])

plt.show()
