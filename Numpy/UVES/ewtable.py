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
import argmaxmin
from gatspy.periodic import LombScargle

SECSPERDAY = 3600.0 * 24.0

coltype = dict(ew = 2, ps = 4, pr = 6)

parsearg = argparse.ArgumentParser(description='Process UVES data to produce a table of how EW is affected by X-ray')
parsearg.add_argument('inoutfiles', type=str, nargs='+', help='EW data produced by uvesew and optional output file')
parsearg.add_argument('--type', type=str, default='ew', help='Type of feature to process, ew, ps or pr default ew')
parsearg.add_argument('--splittime', help='Split plot segs on value', type=str, default='1d')
parsearg.add_argument('--xraylevels', type=str, required=True, help='Start:step:Stop or start:stop/number of xray levels')
parsearg.add_argument('--periods', type=str, required=True, help='Range of periods to look for')
parsearg.add_argument('--maxnum', type=int, default=1, help='Number of L-S periodogram maxima to find')
parsearg.add_argument('--errorlev', type=float, default=0.5, help='Error parameter')
parsearg.add_argument('--abs', action='store_false', help='Take abs value of result')

resargs = vars(parsearg.parse_args())

inoutfiles = resargs['inoutfiles']
if len(inoutfiles) > 2:
    print "Expecting input file or input output"
    sys.exit(8)
if len(inoutfiles) == 2:
    ewfile, outfile = inoutfiles
else:
    ewfile = inoutfiles[0]
    outfile = None

typeplt = resargs['type']
splitem = periodarg.periodarg(resargs['splittime'])
xraylevels = periodarg.periodrange(resargs['xraylevels'])
lsperiods = periodarg.periodrange(resargs['periods'])
errorlev = resargs['errorlev']
abss = resargs['abs']
nmax = resargs['maxnum']

try:
    typecol = coltype[typeplt]
except ValueError:
    print "Invalid column type", typeplt

# Now read the EW file
# This is dates, barycentric dates, EWs, PSes, PR (value and error pairs) interpolated xray amp and gradients

try:
    inputdata = np.loadtxt(ewfile, unpack=True)
    jdates = inputdata[0]
    bjdates = inputdata[1]
    values = inputdata[typecol]
    xrayvs = inputdata[8]
except IOError as e:
    print "Cannot open info file, error was", e.args[1]
    sys.exit(10)
except IndexError, ValueError:
    print "Input data wrong format"
    sys.exit(12)

datelist = [jdate.jdate_to_datetime(jd) for jd in jdates]
dateparts = splittime.splittime(splitem, datelist, jdates, bjdates, values, xrayvs)


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
