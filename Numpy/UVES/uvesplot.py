#! /usr/bin/env python

# Apply X-ray file to UVES data to mark

import sys
import os
import string
import os.path
import locale
import argparse
import numpy as np
import miscutils
import jdate
import datetime
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import dates
import levelselect
import splittime
import histandgauss

SECSPERDAY = 3600.0 * 24.0

parsearg = argparse.ArgumentParser(description='Process UVES data and show plots of effectively suppressing where X-ray levels are high')
parsearg.add_argument('--ewfile', type=str, required=True, help='EW data produced by uvesew')
parsearg.add_argument('--xrayfile', type=str, nargs='*', help='Xray data files')
parsearg.add_argument('--xrayoffset', type=float, default=0.0, help='Offset to X-ray times')
parsearg.add_argument('--logxray', action='store_true', help='Display X-rays on log scale')
parsearg.add_argument('--width', help="Width of plot", type=float, default=8)
parsearg.add_argument('--height', help="Height of plot", type=float, default=8)
parsearg.add_argument('--hwidth', help="Width of histogram", type=float, default=10)
parsearg.add_argument('--splittime', help='Split plot segs on value', type=float, default=1e10)
parsearg.add_argument('--hheight', help="Height of histogram", type=float, default=8)
parsearg.add_argument('--bins', help='Histogram bins', type=int, default=20)
parsearg.add_argument('--colours', help='Colours for plot', type=str, default='blue,green,red,black,purple,orange')
parsearg.add_argument('--outfile', help='Prefix for output file', type=str)
parsearg.add_argument('xraylevel', type=str, nargs='+', help='Level of xray activity at which we discount data')

resargs = vars(parsearg.parse_args())

ewfile = resargs['ewfile']
xrayfiles = resargs['xrayfile']
width = resargs['width']
height = resargs['height']
hwidth = resargs['hwidth']
hheight = resargs['hheight']
bins = resargs['bins']
logxray = resargs['logxray']
xrayoffset = resargs['xrayoffset']
xraylevelargs = resargs['xraylevel']
colours = string.split(resargs['colours'], ',')
splitem = resargs['splittime']
outfile = resargs['outfile']

# Decipher xray levels

xraylevels = levelselect.levelselect(xraylevelargs)
if xraylevels is None:
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

# Kick off by reading in X-ray data also work out gradient

xraydata = []
maxamp = 0
mingrad = 1e20
maxgrad = -1e20

for daynum, xrf in enumerate(xrayfiles):
    try:
        
        # Columns of file are amplitude, error (currently ignored) and time.
        # Time is seconds since 1/1/98 midnight don't ask me why.
         
        xray_amp, xray_err, xray_time = np.loadtxt(xrf, unpack=True)

        xray_time += xrayoffset
        xray_time /= SECSPERDAY
        xray_time += 50814.0            # 1/1/1998 for whatever reason
        
        # Get the difference between observations
        # Work out the gradient
        
        xray_timediff = np.mean(np.diff(xray_time))
        xray_gradient = np.gradient(xray_amp, xray_timediff)
        
        maxamp = max(maxamp, np.max(xray_amp))
        mingrad = min(mingrad, np.min(xray_gradient))
        maxgrad = max(maxgrad, np.max(xray_gradient))
        
        # Get sates as datetime array
        
        xray_dates = [jdate.jdate_to_datetime(d) for d in xray_time] 
        
    except IOError as e:
        print "Cannoot open", xrf, "Error was", e.args[1]
        sys.exit(11)
    
    # Get ourselves an array of 3 rows with 4 columns, times, amps, gradients and times converted to dates
     
    xraydata.append((xray_time, xray_amp, xray_gradient, xray_dates))

# Formatting operation to display times as hh:mm

hfmt = dates.DateFormatter('%H:%M')

# Display of X-ray values

fig = plt.figure(figsize=(width, height))
fig.canvas.set_window_title("Xray values all to same scale")
ln = 1
commonax = None
plt.subplots_adjust(hspace = 0)

for xray_time, xray_amp, xray_gradient, xray_dates in xraydata:
    
    # Display of one column 3 axes
    
    ax1 = plt.subplot(3, 1, ln, sharex=commonax)
    if commonax is None: commonax=ax1
    
    # Limit each display to maxamp as we worked out when we read it in
    
    plt.ylim(0, maxamp)
    ax1.xaxis.set_major_formatter(hfmt)
    fig.autofmt_xdate()
    
    # Recalc this to put them on the same axis
    
    xray_dates = np.array([jdate.jdate_to_datetime(d - ln*2 - 2) for d in xray_time])
    if logxray:
        plt.semilogy(xray_dates, xray_amp, color='black')
    else:
        plt.plot(xray_dates, xray_amp, color='black')

    plt.legend(["Day %d" % ln])
    plt.xlabel('Time')
    plt.ylabel('Intensity')
    rax = plt.twinx(ax1)
    plt.ylim(mingrad, maxgrad)
    plt.plot(xray_dates, xray_gradient, color='purple', ls=':')
    plt.ylabel('Gradient')
    rax.yaxis.label.set_color('purple')
    rax.tick_params(axis='y', colors='purple')
    ln += 1

if outfile is not None:
    fig.savefig(outfile + '-xraydisp.png')

# Now read the EW file
# This is dates, barycentric dates (not currently used), EWs, interpolated amp and gradients

try:
    
    jdates, bjdates, ews, prs, xrayvs, xraygrads = np.loadtxt(ewfile, unpack=True)
    
except IOError as e:
    print "Cannot open info file, error was", e.args[1]
    sys.exit(12)

# Get date list and split up spectra by day

datelist = [jdate.jdate_to_datetime(jd) for jd in jdates]
dateparts = splittime.splittime(SECSPERDAY, datelist, ews, prs, xrayvs, xraygrads)

# Create legends for each specified level
# Remember the selected EWs for each level

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

for day_dates, day_ews, day_prs, day_xrayvs, day_xraygrads in dateparts:
    
    minew = np.min(day_ews)
    maxew = np.max(day_ews)
    
    xray_time, xray_amp, xray_gradient, xray_dates = xraydata.pop(0)
    
    fig = plt.figure(figsize=(width,height))   
    plt.subplots_adjust(hspace = 0)    
    plt.xlim(day_dates[0], day_dates[-1])
    fig.canvas.set_window_title(day_dates[0].strftime("For %d %b %Y"))
    
    ax1 = None
    
    # We remember the selected EWs for each X-ray level in "ewforday"
    
    ewforday = []
    
    for ln, xrl in enumerate(xraylevels):
        pax = plt.subplot(1+nlevs,1,1+ln, sharex=ax1)
        plt.ylim(minew, maxew)
        if ax1 is None: ax1=pax
        minxr, maxxr, isg = xrl
        if isg:
            selection = (day_xraygrads > minxr) & (day_xraygrads < maxxr)
        else:
            selection = (day_xrayvs > minxr) & (day_xrayvs < maxxr)

        plot_ews = day_ews[selection]
        plot_times = day_dates[selection]
        
        for t,e in splittime.splittime(splitem, plot_times, plot_ews):
            plt.plot(t, e, color=colours[ln])
        
        for t,pr in zip(day_dates, day_prs):
            if pr < 1.0:
                plt.axvline(t, color='#102590', alpha=.5)
        plt.legend([legends[ln]])
        
        # Append EWs to that for day and total for X-ray level
        
        ewforday.append(plot_ews)
        ewlevs[ln] = np.append(ewlevs[ln], plot_ews)
  
    # Stick X-ray plot at the bottom
    
    ax2 = plt.subplot(1+nlevs,1,1+nlevs,sharex=ax1)

    if logxray:
        plt.semilogy(xray_dates, xray_amp)
    else:    
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
    
    # Overlay gradient plot
    
    ax3 = plt.twinx(ax2)
    plt.plot(xray_dates, xray_gradient, color='purple', ls=':')
    #plt.legend(['X-ray grad'])
    for ln, xrl in enumerate(xraylevels):
        minxr, maxxr, isg = xrl
        if isg:
            if minxr > -1e30: plt.axhline(minxr, color=colours[ln], ls=':')
            if maxxr < 1e30: plt.axhline(maxxr, color=colours[ln], ls=':')
    
    if outfile is not None:
        fig.savefig(outfile + day_dates[0].strftime("plot_%d%b.png"))
    
    # Do EW histograms for day.
    # We recorded the selected EW for each x-ray level in ewlevs
    # First a combined histogram
    
    fig = plt.figure(figsize=(hwidth, hheight))
    fig.canvas.set_window_title(day_dates[0].strftime("Equivalent widths for %d %b %Y combined"))
    plt.hist(ewforday, bins=bins)
    plt.legend(legends)
    if outfile is not None:
        fig.savefig(outfile + day_dates[0].strftime("cewhist_%d%b.png"))
    
    # Redo as a separate histogram for each day
    
    fig = plt.figure(figsize=(hwidth, hheight))   
    plt.subplots_adjust(hspace = 0)
    fig.canvas.set_window_title(day_dates[0].strftime("Equivalent widths for %d %b %Y"))
    plt.subplots_adjust(hspace = 0)
    ax1 = None
    for ln, ewd in enumerate(ewforday):
        ax = plt.subplot(nlevs, 1, 1+ln, sharex=ax1)
        histandgauss.histandgauss(ewd, bins=bins, colour=colours[ln])
        if ax1 is None: ax1 = ax
        plt.legend([legends[ln]])
    if outfile is not None:
        fig.savefig(outfile + day_dates[0].strftime("ewhist_%d%b.png"))

# Finally do a histogram for all days combined
# One histogram with different bars for each X-ray level

fig = plt.figure(figsize=(hwidth, hheight))
fig.canvas.set_window_title("Equivalent widths (all days) combined")
plt.hist(ewlevs, bins=bins)
plt.legend(legends)
if outfile is not None:
    fig.savefig(outfile + "cewhistall.png")

# Now redo as separate histograms for each level

fig = plt.figure(figsize=(hwidth, hheight))
fig.canvas.set_window_title("Equivalent widths (all days)")
plt.subplots_adjust(hspace = 0)
ax1 = None
for ln, ewd in enumerate(ewlevs):
    ax = plt.subplot(nlevs, 1, 1+ln, sharex=ax1)
    histandgauss.histandgauss(ewd, bins=bins, colour=colours[ln])
    if ax1 is None: ax1 = ax
    plt.legend([legends[ln]])
if outfile is not None:
    fig.savefig(outfile + "ewhistall.png")
    
# Only display if we're not saving

if outfile is None:
    plt.show()
