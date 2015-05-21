#! /usr/bin/env python

# Apply X-ray file to UVES data to mark

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
import specdatactrl
import datarange
import jdate
import meanval
import datetime
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import dates
import splittime

SECSPERDAY = 3600.0 * 24.0

parsearg = argparse.ArgumentParser(description='Process UVES data and show plots of effectively suppressing where X-ray levels are high')
parsearg.add_argument('--ctrl', type=str, help='Input control file', required=True)
parsearg.add_argument('--rangefile', type=str, help='Range file')
parsearg.add_argument('--rangename', type=str, default='halpha', help='Range name to calculate equivalent widths')
parsearg.add_argument('--xrayfile', type=str, nargs='*', help='Xray data files')
parsearg.add_argument('--xrayoffset', type=float, default=0.0, help='Offset to X-ray times')
parsearg.add_argument('--width', help="Width of plot", type=float, default=8)
parsearg.add_argument('--height', help="Height of plot", type=float, default=8)
parsearg.add_argument('--hwidth', help="Width of histogram", type=float, default=10)
parsearg.add_argument('--splittime', help='Split plot segs on value', type=float, default=1e10)
parsearg.add_argument('--hheight', help="Height of histogram", type=float, default=8)
parsearg.add_argument('--bins', help='Histogram bins', type=int, default=20)
parsearg.add_argument('--colours', help='Colours for plot', type=str, default='blue,green,red,black,purple,orange')
parsearg.add_argument('--barycentric', action='store_true', help='Use barycentric date/time now obs date/time')
parsearg.add_argument('--outfile', help='Prefix for output file', type=str)
parsearg.add_argument('xraylevel', type=str, nargs='+', help='Level of xray activity at which we discount data')

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
xrayoffset = resargs['xrayoffset']
baycent = resargs['barycentric']
xraylevelargs = resargs['xraylevel']
colours = string.split(resargs['colours'], ',')
splitem = resargs['splittime']
outfile = resargs['outfile']

# Xray levels to plot from are given as:
# This code interprets the following arguments:

# n (+ve value) upper limit of n
# n (-ve value) lower limit of -n (unless we are talking about gradients when upper limit of n)
# m,n lower limit m upper limit n
# m, lower limit of m
# ,n upper limit of n
# Prefix by g: to talk about gradients (or l: to specify level).

levmatcher = re.compile('^(?:([gl]):)?([-e\d.]*)(,?)([-e\d.]*)$', re.IGNORECASE)

xraylevels = []
for xrl in xraylevelargs:
    try:
        # Initialise to nice big numbers
        lo = -1e40
        hi = 1e40
        
        # Special case of no limit
        if xrl == '0' or xrl == '-':
            xraylevels.append((lo, hi, False))
            continue
        mtch = levmatcher.match(xrl)
        if mtch is None:
            raise ValueError("match")
        
        # re processing sets first group to l, g or None,
        # second group to first numeric or empty
        # third group to comma or empty
        # fourth group to second numeric or empty
        
        lgind, lowarg, comma, hiarg = mtch.groups()
        isg = lgind == 'g'  # Covers case where none at all
        
        if len(hiarg) == 0:     # No second numeric
            
            # If we had a comma, then this is a lower limit
            
            if len(comma) != 0:
                lo = float(lowarg)
            else:
                # Possibly a high limit but low limit if doing gradient
                hip = float(lowarg)
                if not isg and hip < 0.0:
                    lo = -hip
                else:
                    hi = hip
        else:
            # Did have high limit, if we've got lower limit take it
            hi = float(hiarg)
            if len(lowarg) != 0:
                lo = float(lowarg)
        xraylevels.append((lo, hi, isg))
    except ValueError:
        print "Cannot understand limit", xrl
        sys.exit(3)

nlevs = len(xraylevels)

# Make sure there are enough to cover all the xray levels + 1

while nlevs >= len(colours):
    colours = colours * 2

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
        
        xray_dates = np.array([jdate.jdate_to_datetime(d) for d in xray_time])
        
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
        
    xraydata.append((interpfn, ginterpfn, xray_time, xray_amp, xray_gradient, xray_dates))

# This is used for display times as hh:mm

hfmt = dates.DateFormatter('%H:%M')

# Display of X-ray values

fig = plt.figure(figsize=(width, height))
fig.canvas.set_window_title("Xray values all to same scale")
ln = 1
commonax = None
plt.subplots_adjust(hspace = 0)

for xrd in xraydata:
    ax1 = plt.subplot(3, 1, ln, sharex=commonax)
    if commonax is None: commonax=ax1
    ifn, gifn, xray_time, xray_amp, xray_gradient, xray_dates = xrd
    plt.ylim(0, maxamp)
    ax1.xaxis.set_major_formatter(hfmt)
    fig.autofmt_xdate()
    xray_dates = np.array([jdate.jdate_to_datetime(d - ln*2 - 2) for d in xray_time])
    plt.plot(xray_dates, xray_amp, color='black')
    plt.legend(["Day %d" % ln])
    plt.xlabel('Time')
    plt.ylabel('Intensity')
    rax = plt.twinx(ax1)
    plt.ylim(mingrad, maxgrad)
    plt.plot(xray_dates, xray_gradient, color='purple', ls='--')
    plt.ylabel('Gradient')
    rax.yaxis.label.set_color('purple')
    rax.tick_params(axis='y', colors='purple')
    ln += 1

if outfile is not None:
    fig.savefig(outfile + '-xraydisp.png')

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

# Split up spectra according to day

daydata = []
cday = []
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

# Create legends for each specified level

legends = []
ewlevs = []

for minxr, maxxr, isg in xraylevels:
    ewlevs.append(np.empty(0,))
    if minxr <= -1e30:
        if maxxr >= 1e30:
            leg = "No X-ray"
        else:
            leg = "X-ray < %.3g" % maxxr
    elif maxxr >= 1e30:
        leg = "X-ray > %.3g" % minxr
    else:
        leg = "%.3g > X-ray > %.3g" % (maxxr, minxr)
    if isg:
        leg += " (gr)"
    legends.append(leg)

# Plot for each day

for cday in daydata:
    
    xrd = xraydata.pop(0)
    interpfn, ginterpfn, xray_time, xray_amp, xray_gradient, xray_dates = xrd
    
    fig = plt.figure(figsize=(width,height))   
    plt.subplots_adjust(hspace = 0)
    
    add = np.array(cday)
    day_jdates, day_bjdates, day_ews = add.transpose()
    day_dates = np.array([jdate.jdate_to_datetime(d) for d in day_jdates])
    day_xraylev = interpfn(day_jdates)
    day_xraygrad = ginterpfn(day_jdates)
    
    plt.xlim(day_dates[0], day_dates[-1])
    fig.canvas.set_window_title(day_dates[0].strftime("For %d %b %Y"))
    
    ax1 = None
    
    ewforday = []
    
    for ln, xrl in enumerate(xraylevels):
        pax = plt.subplot(1+nlevs,1,1+ln, sharex=ax1)
        plt.ylim(minew, maxew)
        if ax1 is None: ax1=pax
        minxr, maxxr, isg = xrl
        if isg:
            selection = (day_xraygrad > minxr) & (day_xraygrad < maxxr)
        else:
            selection = (day_xraylev > minxr) & (day_xraylev < maxxr)

        plot_ews = day_ews[selection]
        plot_times = day_dates[selection]
        
        for t,e in splittime.splittime(plot_times, plot_ews, splitem):
            plt.plot(t, e, color=colours[ln])
        plt.legend([legends[ln]])
        # Append EWs to that for day and total for level
        ewforday.append(plot_ews)
        ewlevs[ln] = np.append(ewlevs[ln], plot_ews)
  
    # Stick X-ray stuff at the bottom
    
    ax2 = plt.subplot(1+nlevs,1,1+nlevs,sharex=ax1)
    
    plt.plot(xray_dates, xray_amp)
    for ln, xrl in enumerate(xraylevels):
        minxr, maxxr, isg = xrl
        if not isg:
            if minxr > -1e30: plt.axhline(minxr, color=colours[ln])
            if maxxr < 1e30: plt.axhline(maxxr, color=colours[ln])
    plt.legend(["X-ray amp"])
    plt.xlim(xray_dates[0], xray_dates[-1])
    ax2.xaxis.set_major_formatter(hfmt)
    plt.gcf().autofmt_xdate()
    ax3 = plt.twinx(ax2)
    plt.plot(xray_dates, xray_gradient, color='purple', ls='--')
    #plt.legend(['X-ray grad'])
    for ln, xrl in enumerate(xraylevels):
        minxr, maxxr, isg = xrl
        if isg:
            if minxr > -1e30: plt.axhline(minxr, color=colours[ln], ls='--')
            if maxxr < 1e30: plt.axhline(maxxr, color=colours[ln], ls='--')
    
    if outfile is not None:
        fig.savefig(outfile + day_dates[0].strftime("plot_%d%b.png"))
    
    # Do EW histograms for day
    
    fig = plt.figure(figsize=(hwidth, hheight))
    fig.canvas.set_window_title(day_dates[0].strftime("Equivalent widths for %d %b %Y combined"))
    plt.hist(ewforday, normed=True)
    plt.legend(legends)
    if outfile is not None:
        fig.savefig(outfile + day_dates[0].strftime("cewhist_%d%b.png"))
    
    fig = plt.figure(figsize=(hwidth, hheight))   
    plt.subplots_adjust(hspace = 0)
    fig.canvas.set_window_title(day_dates[0].strftime("Equivalent widths for %d %b %Y"))
    plt.subplots_adjust(hspace = 0)
    ax1 = None
    for ln, ewd in enumerate(ewforday):
        ax = plt.subplot(nlevs, 1, 1+ln, sharex=ax1)
        plt.hist(ewd, bins=bins, color=colours[ln], normed=True)
        if ax1 is None: ax1 = ax
        plt.legend([legends[ln]])
    if outfile is not None:
        fig.savefig(outfile + day_dates[0].strftime("ewhist_%d%b.png"))

fig = plt.figure(figsize=(hwidth, hheight))
fig.canvas.set_window_title("Equivalent widths (all days) combined")
plt.hist(ewlevs, normed=True)
plt.legend(legends)
if outfile is not None:
    fig.savefig(outfile + "cewhistall.png")
fig = plt.figure(figsize=(hwidth, hheight))
fig.canvas.set_window_title("Equivalent widths (all days)")
plt.subplots_adjust(hspace = 0)
ax1 = None
for ln, ewd in enumerate(ewlevs):
    ax = plt.subplot(nlevs, 1, 1+ln, sharex=ax1)
    plt.hist(ewd, bins=bins, color=colours[ln], normed=True)
    if ax1 is None: ax1 = ax
    plt.legend([legends[ln]])
if outfile is not None:
    fig.savefig(outfile + "ewhistall.png")
plt.show()
