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

parsearg = argparse.ArgumentParser(description='Process UVES data and show plots third version', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('--ewfile', type=str, required=True, help='EW data produced by uvesew')
parsearg.add_argument('--xrayfile', type=str, nargs='*', help='Xray data files')
parsearg.add_argument('--xrayoffset', type=float, default=0.0, help='Offset to X-ray times')
parsearg.add_argument('--width', help="Width of plot", type=float, default=8)
parsearg.add_argument('--height', help="Height of plot", type=float, default=8)
parsearg.add_argument('--outfile', help='Prefix for output file', type=str)
parsearg.add_argument('--padtopmult', type=float, default=1.03, help='Multiply maxima in PR and EW total display')
parsearg.add_argument('--padbotmult', type=float, default=0.97, help='Multiply minima in PR and EW total display')

resargs = vars(parsearg.parse_args())

ewfile = resargs['ewfile']
xrayfiles = resargs['xrayfile']
width = resargs['width']
height = resargs['height']
outfile = resargs['outfile']
xrayoffset = resargs['xrayoffset']
padt = resargs['padtopmult']
padb = resargs['padbotmult']
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
    plt.errorbar(xray_dates, xray_amp, yerr=xray_err, ecolor='red', color='black')

    plt.legend(["Day %d" % ln], loc='best')
    plt.xlabel('Time')
    plt.ylabel('C/s')
    #rax = plt.twinx(ax1)
    #plt.ylim(mingrad, maxgrad)
    #plt.plot(xray_dates, xray_gradient, color='purple', ls=':')
    #plt.ylabel('Gradient')
    #rax.yaxis.label.set_color('purple')
    #rax.tick_params(axis='y', colors='purple')
    ln += 1

fig.tight_layout()
plt.subplots_adjust(hspace = 0)
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

maxew = ews.max()
maxpr = prs.max()
minew = ews.min()
minpr = prs.min()

# Get date list and split up spectra by day

datelist = [jdate.jdate_to_datetime(jd) for jd in jdates]
dateparts = splittime.splittime(SECSPERDAY, datelist, ews, prs, xrayvs, xraygrads)

# Plot for each day

for day_dates, day_ews, day_prs, day_xrayvs, day_xraygrads in dateparts:

    xray_time, xray_amp, xray_err, xray_gradient, xray_dates = xraydata.pop(0)

    datedescr = day_dates[0].strftime("%d %b %Y")
    dateshort = day_dates[0].strftime("%d%b")

    fig = plt.figure(figsize=(width,height))
    plt.xlim(day_dates[0], day_dates[-1])
    fig.canvas.manager.set_window_title("Plotting for " + datedescr)
    ax1 = plt.subplot(3, 1, 1)

    plt.ylabel('EW ($\AA$)')
    plt.plot(day_dates, day_ews, color='blue')
    plt.legend(['EWs'], loc='best')

    ax2 = plt.subplot(3, 1, 2, sharex=ax1)
    plt.ylabel("ratio")
    plt.plot(day_dates, day_prs, color='purple')
    plt.legend(['PRs'], loc='best')

    ax3 = plt.subplot(3, 1, 3, sharex=ax1)

    plt.ylabel('c/s')
    plt.plot(xray_dates, xray_amp, color='black')
    plt.legend(["X-ray c/s"], loc='best')
    plt.xlim(xray_dates[0], xray_dates[-1])
    ax2.xaxis.set_major_formatter(hfmt)
    plt.gcf().autofmt_xdate()
    plt.xlabel("Time")
    fig.tight_layout()
    plt.subplots_adjust(hspace = 0)
    
    if outfile is not None:
        newf = outfile + "plot_" + dateshort + ".png"
        fig.savefig(newf)
        filesmade.append(newf)

# Repeat with EWs all on same scale

fig = plt.figure(figsize=(width, height))
fig.canvas.manager.set_window_title("EWs all to same scale")
ln = 1
commonax = None

for day_dates, day_ews, day_prs, day_xrayvs, day_xraygrads in dateparts:
    
    # Display of one column 3 axes

    ax1 = plt.subplot(3, 1, ln, sharex=commonax)
    if commonax is None: commonax=ax1

    # Limit each display to maxamp as we worked out when we read it in

    plt.ylim(minew*padb, maxew*padt)
    ax1.xaxis.set_major_formatter(hfmt)
    fig.autofmt_xdate()

    # Recalc this to put them on the same axis

    day_dates = np.array([jdate.jdate_to_datetime(jdate.datetime_to_jdate(d) - ln*2 - 2) for d in day_dates])
    plt.plot(day_dates, day_ews, color='blue')

    plt.legend(["Day %d" % ln], loc='best')
    plt.xlabel('Time')
    plt.ylabel('EW ($\AA$)')
    ln += 1

fig.tight_layout()
plt.subplots_adjust(hspace = 0)

if outfile is not None:
    newf = outfile + '-allew.png'
    fig.savefig(newf)
    filesmade.append(newf)

# Repeat with PRs all on same scale

fig = plt.figure(figsize=(width, height))
fig.canvas.manager.set_window_title("PRs all to same scale")
ln = 1
commonax = None

for day_dates, day_ews, day_prs, day_xrayvs, day_xraygrads in dateparts:
    
    # Display of one column 3 axes

    ax1 = plt.subplot(3, 1, ln, sharex=commonax)
    if commonax is None: commonax=ax1

    # Limit each display to maxamp as we worked out when we read it in

    plt.ylim(minpr*padb, maxpr*padt)
    ax1.xaxis.set_major_formatter(hfmt)
    fig.autofmt_xdate()

    # Recalc this to put them on the same axis

    day_dates = np.array([jdate.jdate_to_datetime(jdate.datetime_to_jdate(d) - ln*2 - 2) for d in day_dates])
    plt.plot(day_dates, day_prs, color='purple')

    plt.legend(["Day %d" % ln], loc='best')
    plt.xlabel('Time')
    plt.ylabel('PR')
    ln += 1

fig.tight_layout()
plt.subplots_adjust(hspace = 0)

if outfile is not None:
    newf = outfile + '-allpr.png'
    fig.savefig(newf)
    filesmade.append(newf)

# Only display if we're not saving

if outfile is None:
    plt.show()
