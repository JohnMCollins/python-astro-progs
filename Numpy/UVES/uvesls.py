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
import splittime
import periodarg
import scipy.signal as ss

SECSPERDAY = 3600.0 * 24.0

coltype = dict(ew = 2, ps = 4, pr = 6)

parsearg = argparse.ArgumentParser(description='Process UVES EW data and generate periodograms')
parsearg.add_argument('ewfile', type=str, nargs=1, help='EW data produced by uvesew')
parsearg.add_argument('--xrayfile', type=str, nargs='*', help='Xray data files')
parsearg.add_argument('--xraylevel', type=float, required=True, help='X-ray level for cutoff')
parsearg.add_argument('--xrayoffset', type=float, default=0.0, help='Offset to X-ray times')
parsearg.add_argument('--splittime', help='Split plot segs on value', type=float, default=1)
parsearg.add_argument('--outfile', help='Prefix for output file', type=str, required=True)
parsearg.add_argument('--start', help='Starting period to try', type=str, default='10m')
parsearg.add_argument('--step', help='Step in periods to try', type=str, default='10s')
parsearg.add_argument('--stop', help='Ending period to try', type=str, default='1d')
parsearg.add_argument('--type', type=str, default='ew', help='Type of feature to process, ew, ps or pr default ew'

resargs = vars(parsearg.parse_args())

ewfile = resargs['ewfile']
xrayfiles = resargs['xrayfile']
xrayoffset = resargs['xrayoffset']
xraylevel = resargs['xraylevel']
splitem = resargs['splittime']
outfile = resargs['outfile']
typeplt = resargs['type']

try:
    typecol = coltype[typeplt]
except ValueError:
    print "Invalid column type", typeplt

try:
    startper = periodarg.periodarg(resargs['start'])
    stepper = periodarg.periodarg([resargs['step']])
    stopper = periodarg.periodarg([resargs['stop']])
except ValueError as e:
    print "Trouble with period argument set"
    print "Error was:", e.args[0]
    sys.exit(8)

if startper >= stopper:
    print "Sorry do not understand start period >= stop period"
    sys.exit(9)
    
perrange = np.arange(startper, stopper, stepper)
tfreqs = 2 * np.pi / perrange

if len(perrange) <= 10:
    print "Range of periods is unacceptably low"
    sys.exit(9)

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

# Now read the EW file we need the dates to marry with the xray and the barycentric dates for the calc.

try:
    filecontents = np.loadtxt(ewfile, unpack=True)
    
    jdates = filecontents[0]
    bjdates = filecontents[1]
    values = filecontents[typecol]
    xrayvs = filecontents[9]

except IOError as e:
    print "Cannot open info file, error was", e.args[1]
    sys.exit(12)
except IndexError as e:
    print "File does not seem to be correct format"
    sys.exit(13)

# Get date list and split up spectra by day

datelist = [jdate.jdate_to_datetime(jd) for jd in jdates]
dateparts = splittime.splittime(SECSPERDAY * splitem, datelist, jdates, bjdates, values, xrayvs)

# Produce individual files if number of days > 1

if len(dateparts) > 1:
    
    
    sel = xrayvs <= xraylevel
    
    sel_datelist = datelist[sel]
    sel_jdates = jdates[sel]
    sel_bjdates = bj

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
    fig.canvas.set_window_title("Plotting for " + datedescr)
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
    fig.canvas.set_window_title("Equivalent widths for " + datedescr + " combined")
    plt.hist(ewforday, bins=bins, color=hc)
    plt.xlabel("Ews for " + datedescr + " " + titlelims)
    plt.legend(legends)
    if outfile is not None:
        newf = outfile + "cewhist_" + dateshort + ".png"
        fig.savefig(newf)
        filesmade.append(newf)
    fig = plt.figure(figsize=(hwidth, hheight))
    fig.canvas.set_window_title("Peak Ratios for " + datedescr + " combined")
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
    fig.canvas.set_window_title("Equivalent widths for " + datedescr)
    plt.subplots_adjust(hspace = 0)
    ax1 = None
    for ln, ewd in enumerate(ewforday):
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
    fig.canvas.set_window_title("Peak ratios for " + datedescr)
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
fig.canvas.set_window_title("Equivalent widths (all days) combined")
plt.hist(ewlevs, bins=bins, color=hc)
plt.xlabel("Equivalent widths for all days combined")
plt.legend(legends)
if outfile is not None:
    fig.savefig(outfile + "cewhistall.png")
fig = plt.figure(figsize=(hwidth, hheight))
fig.canvas.set_window_title("Peak ratios (all days) combined")
plt.hist(prlevs, bins=bins, color=hc)
plt.xlabel("Peak ratios for all days combined")
plt.legend(legends)
if outfile is not None:
    fig.savefig(outfile + "cprhistall.png")

# Now redo as separate histograms for each level

fig = plt.figure(figsize=(hwidth, hheight))
fig.canvas.set_window_title("Equivalent widths (all days)")
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
fig.canvas.set_window_title("Peak ratios (all days)")
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
