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
import matplotlib.pyplot as plt
from matplotlib import dates
import splittime
import histandgauss

SECSPERDAY = 3600.0 * 24.0

parsearg = argparse.ArgumentParser(description='Process UVES data and show plots second version', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('--ewfile', type=str, required=True, help='EW data produced by uvesew')
parsearg.add_argument('--xrayfile', type=str, nargs='*', help='Xray data files')
parsearg.add_argument('--xrayoffset', type=float, default=0.0, help='Offset to X-ray times')
parsearg.add_argument('--logxray', action='store_true', help='Display X-rays on log scale')
parsearg.add_argument('--logpr', action='store_true', help='Take log of peak ratio')
parsearg.add_argument('--width', help="Width of plot", type=float, default=8)
parsearg.add_argument('--height', help="Height of plot", type=float, default=8)
parsearg.add_argument('--hwidth', help="Width of histogram", type=float, default=10)
parsearg.add_argument('--splittime', help='Split plot segs on value', type=float, default=1e10)
parsearg.add_argument('--hheight', help="Height of histogram", type=float, default=8)
parsearg.add_argument('--bins', help='Histogram bins', type=int, default=20)
parsearg.add_argument('--outfile', help='Prefix for output file', type=str)
parsearg.add_argument('--minpoints', help='Minimum number of points to try to plot', type=int, default=10)
parsearg.add_argument('xraylevel', type=float, nargs='+', help='low and high level of X-Rays')

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
xraylevels = resargs['xraylevel']
splitem = resargs['splittime']
outfile = resargs['outfile']
minpoints = resargs['minpoints']

if len(xraylevels) != 2 or xraylevels[0] >= xraylevels[1]:
    print "Invalid X-ray levels should be low and high"
    sys.exit(9)

loxray, hixray = xraylevels

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

    xraydata.append((xray_time, xray_amp, xray_err, xray_gradient, xray_dates))

# Formatting operation to display times as hh:mm

hfmt = dates.DateFormatter('%H:%M')

# Remember files made in case we have to delete them

filesmade = []

# Display of X-ray values

fig = plt.figure(figsize=(width, height))
fig.canvas.manager.set_window_title("Xray values all to same scale")
ln = 1
plt.subplots_adjust(hspace = 0)
commonax = None

for xray_time, xray_amp, xray_err, xray_gradient, xray_dates in xraydata:

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
        plt.errorbar(xray_dates, xray_amp, yerr=xray_err, ecolor='red', color='black')

    plt.legend(["Day %d" % ln])
    plt.xlabel('Time')
    plt.ylabel('Intensity')
    #rax = plt.twinx(ax1)
    #plt.ylim(mingrad, maxgrad)
    #plt.plot(xray_dates, xray_gradient, color='purple', ls=':')
    #plt.ylabel('Gradient')
    #rax.yaxis.label.set_color('purple')
    #rax.tick_params(axis='y', colors='purple')
    ln += 1

if outfile is not None:
    newf = outfile + '-xraydisp.png'
    fig.savefig(newf)
    filesmade.append(newf)

# Now read the EW file
# This is dates, barycentric dates (not currently used), EWs, interpolated amp and gradients

try:

    jdates, bjdates, ews, ewerrs, pses, pserrs, prs, prerrs, xrayvs, xraygrads = np.loadtxt(ewfile, unpack=True)

except IOError as e:
    print "Cannot open info file, error was", e.args[1]
    sys.exit(12)

if resargs['logpr']:
    prs = np.log10(prs)

# Get date list and split up spectra by day

datelist = [jdate.jdate_to_datetime(jd) for jd in jdates]
dateparts = splittime.splittime(SECSPERDAY, datelist, ews, prs, xrayvs, xraygrads)

# Remember the selected EWs for each level

ewlevs = []
ewlevs.append(np.empty(0,))
ewlevs.append(np.empty(0,))
ewlevs.append(np.empty(0,))
prlevs = []
prlevs.append(np.empty(0,))
prlevs.append(np.empty(0,))
prlevs.append(np.empty(0,))

legends = ('Below %.6g' % loxray, '%.6g < Xr < %.6g' % (loxray, hixray), 'Above %.6g' % hixray)
hc = ('red', 'blue', 'green')
titlelims = "separating values where x-ray int. between %#.4g and %#.4g" % (loxray, hixray)

# Plot for each day

for day_dates, day_ews, day_prs, day_xrayvs, day_xraygrads in dateparts:

    xray_time, xray_amp, xray_err, xray_gradient, xray_dates = xraydata.pop(0)

    sello = day_xrayvs < loxray
    selhi = day_xrayvs > hixray
    selmid = ~(sello | selhi)

    nlo = np.count_nonzero(sello)
    nmid = np.count_nonzero(selmid)
    nhi = np.count_nonzero(selhi)

    if nlo < minpoints or nmid < minpoints or nhi < minpoints:
        print "%.2f-%.2f: Too few points, low %d mid %d high %d" % (loxray, hixray, nlo, nmid, nhi)
        for f in filesmade:
            try:
                os.remove(f)
            except IOError:
                pass
        sys.exit(0)

    datedescr = day_dates[0].strftime("%d %b %Y")
    dateshort = day_dates[0].strftime("%d%b")

    fig = plt.figure(figsize=(width,height))
    plt.subplots_adjust(hspace = 0)
    plt.xlim(day_dates[0], day_dates[-1])
    fig.canvas.manager.set_window_title("Plotting for " + datedescr)
    ewforday = []
    prforday = []
    ax1 = plt.subplot(3, 1, 1)

    plt.plot(day_dates, day_ews, color='blue')
    for t in day_dates[selmid]:
        plt.axvline(t, color='red', alpha=.5)
    for t in day_dates[selhi]:
        plt.axvline(t, color='green', alpha=.5)
    plt.legend(['EWs'])

    ax2 = plt.subplot(3, 1, 2, sharex=ax1)
    plt.plot(day_dates, day_prs, color='purple')
    for t in day_dates[selmid]:
        plt.axvline(t, color='red', alpha=.5)
    for t in day_dates[selhi]:
        plt.axvline(t, color='green', alpha=.5)
    plt.legend(['Ratios'])

    ax3 = plt.subplot(3, 1, 3, sharex=ax1)

    if logxray:
        plt.semilogy(xray_dates, xray_amp, color='black')
    else:
        plt.plot(xray_dates, xray_amp, color='black')
    plt.axhline(loxray, color='red')
    plt.axhline(hixray, color='green')
    plt.legend(["X-ray amp"])
    plt.xlim(xray_dates[0], xray_dates[-1])
    ax2.xaxis.set_major_formatter(hfmt)
    plt.gcf().autofmt_xdate()
    plt.xlabel("Ews / Peak ratios / X-ray int " + titlelims)

    ewforday.append(day_ews[sello])
    ewforday.append(day_ews[selmid])
    ewforday.append(day_ews[selhi])
    prforday.append(day_prs[sello])
    prforday.append(day_prs[selmid])
    prforday.append(day_prs[selhi])
    ewlevs[0] = np.append(ewlevs[0], day_ews[sello])
    ewlevs[1] = np.append(ewlevs[1], day_ews[selmid])
    ewlevs[2] = np.append(ewlevs[2], day_ews[selhi])
    prlevs[0] = np.append(prlevs[0], day_prs[sello])
    prlevs[1] = np.append(prlevs[1], day_prs[selmid])
    prlevs[2] = np.append(prlevs[2], day_prs[selhi])

    if outfile is not None:
        newf = outfile + "plot_" + dateshort + ".png"
        fig.savefig(newf)
        filesmade.append(newf)

    # Do EW and PR histograms for day.
    # We recorded the selected EW and PR for each x-ray level in ewlevs and prlevs
    # First a combined histogram

    fig = plt.figure(figsize=(hwidth, hheight))
    fig.canvas.manager.set_window_title("Equivalent widths for " + datedescr + " combined")
    plt.hist(ewforday, bins=bins, color=hc)
    plt.xlabel("Ews for " + datedescr + " " + titlelims)
    plt.legend(legends)
    if outfile is not None:
        newf = outfile + "cewhist_" + dateshort + ".png"
        fig.savefig(newf)
        filesmade.append(newf)
    fig = plt.figure(figsize=(hwidth, hheight))
    fig.canvas.manager.set_window_title("Peak Ratios for " + datedescr + " combined")
    plt.hist(prforday, bins=bins, color=hc)
    plt.xlabel("Ratios for " + datedescr + " " + titlelims)
    plt.legend(legends)
    if outfile is not None:
        newf = outfile + "cprhist_" + dateshort + ".png"
        fig.savefig(newf)
        filesmade.append(newf)

    # Redo as a separate histogram for each day

    fig = plt.figure(figsize=(hwidth, hheight))
    plt.subplots_adjust(hspace = 0)
    fig.canvas.manager.set_window_title("Equivalent widths for " + datedescr)
    plt.subplots_adjust(hspace = 0)
    ax1 = None
    for ln, ewd in enumerate(ewforday):, formatter_class=argparse.ArgumentDefaultsHelpFormatter
        ax = plt.subplot(3, 1, 1+ln, sharex=ax1)
        histandgauss.histandgauss(ewd, bins=bins, colour=hc[ln])
        plt.legend([legends[ln]])
        if ax1 is None: ax1 = ax
    plt.xlabel("Ews for " + datedescr + " " + titlelims)
    if outfile is not None:
        newf = outfile + "ewhist_" + dateshort + ".png"
        fig.savefig(newf)
        filesmade.append(newf)

    # And for prs

    fig = plt.figure(figsize=(hwidth, hheight))
    plt.subplots_adjust(hspace = 0)
    fig.canvas.manager.set_window_title("Peak ratios for " + datedescr)
    plt.subplots_adjust(hspace = 0)
    ax1 = None
    for ln, prd in enumerate(prforday):
        ax = plt.subplot(3, 1, 1+ln, sharex=ax1)
        histandgauss.histandgauss(prd, bins=bins, colour=hc[ln])
        plt.legend([legends[ln]])
        if ax1 is None: ax1 = ax
    plt.xlabel("Ratios for " + datedescr + " " + titlelims)
    if outfile is not None:
        newf = outfile + "prhist_" + dateshort + ".png"
        fig.savefig(newf)
        filesmade.append(newf)

# Finally do a histogram for all days combined
# One histogram with different bars for each X-ray level

fig = plt.figure(figsize=(hwidth, hheight))
fig.canvas.manager.set_window_title("Equivalent widths (all days) combined")
plt.hist(ewlevs, bins=bins, color=hc)
plt.xlabel("Equivalent widths for all days combined")
plt.legend(legends)
if outfile is not None:
    fig.savefig(outfile + "cewhistall.png")
fig = plt.figure(figsize=(hwidth, hheight))
fig.canvas.manager.set_window_title("Peak ratios (all days) combined")
plt.hist(prlevs, bins=bins, color=hc)
plt.xlabel("Peak ratios for all days combined")
plt.legend(legends)
if outfile is not None:
    fig.savefig(outfile + "cprhistall.png")

# Now redo as separate histograms for each level

fig = plt.figure(figsize=(hwidth, hheight))
fig.canvas.manager.set_window_title("Equivalent widths (all days)")
plt.subplots_adjust(hspace = 0)
ax1 = None
for ln, ewd in enumerate(ewlevs):
    ax = plt.subplot(3, 1, 1+ln, sharex=ax1)
    histandgauss.histandgauss(ewd, bins=bins, colour=hc[ln])
    plt.legend([legends[ln]])
    if ax1 is None: ax1 = ax
plt.xlabel("Equivalent widths for all days")
if outfile is not None:
    fig.savefig(outfile + "ewhistall.png")

fig = plt.figure(figsize=(hwidth, hheight))
fig.canvas.manager.set_window_title("Peak ratios (all days)")
plt.subplots_adjust(hspace = 0)
ax1 = None
for ln, prd in enumerate(prlevs):
    ax = plt.subplot(3, 1, 1+ln, sharex=ax1)
    histandgauss.histandgauss(prd, bins=bins, colour=hc[ln])
    plt.legend([legends[ln]])
    if ax1 is None: ax1 = ax
plt.xlabel("Peak ratios for all days")
if outfile is not None:
    fig.savefig(outfile + "prhistall.png")

# Only display if we're not saving

if outfile is None:
    plt.show()
