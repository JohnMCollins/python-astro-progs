#! /usr/bin/env python

# Integrate the H alpha peaks to get figures for the total values,
# assume continuum is normalised at 1 unless otherwise specified

import argparse
import os.path
import sys
import string
import numpy as np
import scipy.stats as ss
import matplotlib.pyplot as plt
from matplotlib import dates
import datetime
import exclusions
import jdate
import rangearg
import histandgauss

# According to type of display select column, xlabel  for hist, ylabel for plot

optdict = dict(ew = (2, 'Equivalent width ($\AA$)', 'Equivalent width ($\AA$)'),
               ps = (4, 'Peak size (rel to EW)', 'Peak size (rel to EW)'),
               pr = (6, 'Peak ratio', 'Peak ratio'))

parsearg = argparse.ArgumentParser(description='Plot equivalent width results')
parsearg.add_argument('integ', type=str, nargs=1, help='Input integration file (time/intensity)')
parsearg.add_argument('--title', type=str, default='Equivalent widths', help='Title for window')
parsearg.add_argument('--width', type=float, default=4, help='Display width')
parsearg.add_argument('--height', type=float, default=3, help='Display height')
parsearg.add_argument('--type', help='ew/ps/pr to select display', type=str, default="ew")
parsearg.add_argument('--log', action='store_true', help='Take log of values to plot')
parsearg.add_argument('--sdplot', action='store_true', help='Put separate days in separate figures')
parsearg.add_argument('--sepdays', type=int, default=10000, help='Separate plots if this number of days apart')
parsearg.add_argument('--bins', type=int, default=20, help='Histogram bins')
parsearg.add_argument('--clip', type=float, default=0.0, help='Number of S.D.s to clip from histogram')
parsearg.add_argument('--gauss', action='store_true', help='Normalise and overlay gaussian on histogram')
parsearg.add_argument('--xtype', type=str, default='auto', help='Type X axis - time/date/full/days')
parsearg.add_argument('--xhist', type=str, help='Label for histogram X axis')
parsearg.add_argument('--yhist', type=str, default='Occurrences', help='Label for histogram Y axis')
parsearg.add_argument('--xplot', type=str, help='Label for plot X axis')
parsearg.add_argument('--yplot', type=str, help='Label for plot Y axis')
parsearg.add_argument('--xaxt', action='store_true', help='Put X axis label on top')
parsearg.add_argument('--yaxr', action='store_true', help='Put Y axis label on right')
parsearg.add_argument('--xrange', type=str, help='Range for X axis')
parsearg.add_argument('--yrange', type=str, help='Range for Y axis')
parsearg.add_argument('--histxrange', type=str, help='Range for Hist X axis')
parsearg.add_argument('--histyrange', type=str, help='Range for Hist Y axis')
parsearg.add_argument('--outprefix', type=str, help='Output file prefix')
parsearg.add_argument('--plotcolours', type=str, default='black,red,green,blue,yellow,magenta,cyan', help='Colours for successive plots')
parsearg.add_argument('--excludes', type=str, help='File with excluded obs times and reasons')
parsearg.add_argument('--exclcolours', type=str, default='red,green,blue,yellow,magenta,cyan,black', help='Colours for successive exclude reasons')
parsearg.add_argument('--legend', type=str, help='Specify explicit legend')
parsearg.add_argument('--fork', action='store_true', help='Fork off daemon process to show plot and exit')

res = vars(parsearg.parse_args())
rf = res['integ'][0]
title = res['title']
dims = (res['width'], res['height'])
typeplot = res['type']
takelog = res['log']
sdp = res['sdplot']
sepdays = res['sepdays']
bins = res['bins']
clip = res['clip']
gauss = res['gauss']
xtype = res['xtype']
xtt = res['xaxt']
ytr = res['yaxr']
xrange = rangearg.parserange(res['xrange'])
yrange = rangearg.parserange(res['yrange'])
histxrange = rangearg.parserange(res['histxrange'])
histyrange = rangearg.parserange(res['histyrange'])
outf = res['outprefix']
excludes = res['excludes']
explicit_legend = res['legend']
forkoff = res['fork']

if typeplot not in optdict:
    print "Unknown type", typeplot, "specified"
    sys.exit(2)
ycolumn, histxlab, plotylab = optdict[typeplot]
if res['xhist'] is not None:
    histxlab = res['xhist']
    if histxlab == "none":
        histxlab = ""
if res['yplot'] is not None:
    plotylab = res['yplot']
    if plotylab == "none":
        ylab = ""

# Ones not dependent on column

histylab = res['yhist']
if histylab == "none":
    histylab = ""
    
# Worry about X label for plot later

# Load up EW file and excludes file

if rf is None:
    print "No integration result file specified"
    sys.exit(100)

# If excludes file present load up file and reasons, add in colours

if excludes is not None:
    try:
        elist = exclusions.Exclusions()
        elist.load(excludes)
    except exclusions.ExcludeError as e:
        print e.args[0] + ': ' + e.args[1]
        sys.exit(101)
    rlist = elist.reasons()
    excols = string.split(res['exclcolours'], ',')
    excolours = excols * ((len(rlist) + len(excols) - 1) / len(excols))
    rlookup = dict()
    for r, c in zip(rlist, excolours):
        rlookup[r] = c

# Load up file of integration results

try:
    inp = np.loadtxt(rf, unpack=True)
except IOError as e:
    print "Error loading EW file", rf
    print "Error was", e.args[1]
    sys.exit(102)

if inp.shape[0] != 8:
    print "Expecting new format 8-column shape, please convert"
    print "Shape was", inp.shape
    sys.exit(103)

obsdates = inp[0]
vals = inp[ycolumn]
if takelog and np.min(vals) < 0:
    print "Negative values, cannot take log"
    sys.exit(104)

# If first element is zero, make dates as offset from "now"

if obsdates[0] == 0.0:
    nowt = datetime.datetime.now()
    td = np.vectorize(datetime.timedelta)
    datetimes = now + td(obsdates)
    sim = "(Simulated) "
else:
    td = np.vectorize(jdate.jdate_to_datetime)
    datetimes = td(obsdates)
    sim = ""

xlab = res['xplot']

if xtype == 'time':
    usedt = True
    hfmt = dates.DateFormatter('%H:%M:%S')
    if xlab is None: xlab = datetimes[0].strftime(sim + "Times starting on %d/%m/%y")
elif xtype == 'date':
    usedt = True
    hfmt = dates.DateFormatter('%d/%m/%y')
    if xlab is None: xlab = sim + "Observation dates"
elif xtype == "datetime":
    usedt = True
    hfmt = dates.DateFormatter(sim + "%d/%m/%y %H:%M:%S")
    if xlab is None: xlab = sim + "Observation date/times"
elif xtype == "timedate":
    usedt = True
    hfmt = dates.DateFormatter(sim + "%H:%M:%S %d/%m/%y")
    if xlab is None: xlab = sim + "Observation time/dates"
else:
    usedt = False
    if xlab is None: xlab = sim + "Day offset from start"

fig = plt.figure(figsize=dims)
fig.canvas.set_window_title(title + ' Histogram')

# If clipping histogram, iterate to remove outliers

if clip != 0.0:
    hvals = vals + 0.0
    lh = len(hvals)
    while 1:
        mv = np.mean(hvals)
        std = np.std(hvals)
        sel = np.abs(hvals - mv) <= clip * std
        hvals = hvals[sel]
        nl = len(hvals)
        if nl == 0:
            print "No values left after clip???"
            sys.exit(101)
        if nl == lh:
            break
        lh = nl
    if gauss:
        mv = np.mean(hvals)
        std = np.std(hvals)
        minv = np.min(hvals)
        maxv = np.max(hvals)
        lx = np.linspace(minv,maxv,250)
        garr = ss.norm.pdf(lx, mv, std)
        if histyrange is not None:
            plt.ylim(*histyrange)
        if histxrange is not None:
            plt.xlim(*histxrange)
        plt.hist(hvals, bins=bins, normed = True)
        plt.plot(lx, garr, color='red')
    else:
        if histyrange is not None:
            plt.ylim(*histyrange)
        if histxrange is not None:
            plt.xlim(*histxrange)
        plt.hist(hvals,bins=bins)
else:
    if histyrange is not None:
        plt.ylim(*histyrange)
    if histxrange is not None:
        plt.xlim(*histxrange)
    if gauss:
        mv = np.mean(vals)
        std = np.std(vals)
        minv = np.min(vals)
        maxv = np.max(vals)
        lx = np.linspace(minv, maxv, 250)
        garr = ss.norm.pdf(lx, mv, std)
        plt.hist(vals, bins=bins, normed = True)
        plt.plot(lx, garr, color='red')
    else:
        plt.hist(vals,bins=bins)
if ytr:
    plt.gca().yaxis.tick_right()
    plt.gca().yaxis.set_label_position("right")
if xtt:
    plt.gca().xaxis.tick_top()
    plt.gca().xaxis.set_label_position("top")
if len(histylab) > 0:
    plt.ylabel(histylab)
else:
    plt.yticks([])
if len(histxlab) > 0:
    plt.xlabel(histxlab)
else:
    plt.xticks([])
if explicit_legend is not None:
    plt.legend([explicit_legend], handlelength=0)
if outf is not None:
    fname = outf + '_hist.png'
    plt.savefig(fname)
if not sdp:
    fig = plt.figure(figsize=dims)
    fig.canvas.set_window_title(title + ' Value by time')

rxarray = []
ryarray = []
rxvalues = []
ryvalues = []

lastdate = 1e12

for d, v in zip(dates,vals):
    if d - lastdate > sepdays and len(rxvalues) != 0:
        rxarray.append(rxvalues)
        ryarray.append(ryvalues)
        rxvalues = []
        ryvalues = []
    rxvalues.append(d)
    ryvalues.append(v)
    lastdate = d

if len(rxvalues) != 0:
   rxarray.append(rxvalues)
   ryarray.append(ryvalues)

plotcols = string.split(res['plotcolours'], ',')
colours = plotcols * ((len(rxarray) + len(plotcols) - 1) / len(plotcols))

fnum = 1

if sdp:
    for xarr, yarr, col in zip(rxarray,ryarray,colours):
        offs = xarr[0]
        xa = np.array(xarr) - offs
        ya = np.array(yarr)
        f = plt.figure(figsize=dims)
        f.canvas.set_window_title(title + ' Day ' + str(fnum))
        if xrange is not None:
            plt.xlim(*xrange)
        if yrange is not None:
            plt.ylim(*yrange)
        if len(plotylab) == 0:
            plt.yticks([])
        else:
            if ytr:
                plt.gca().yaxis.tick_right()
                plt.gca().yaxis.set_label_position("right")
            plt.ylabel(plotylab)
        if len(xlab) == 0:
            plt.xticks([])
        else:
            if xtt:
                plt.gca().xaxis.tick_top()
                plt.gca().xaxis.set_label_position('top')
            plt.xlabel(xlab)
        plt.plot(xa,ya,col,label=jdate.display(xarr[0]))
        if excludes is not None:
            sube = elist.inrange(np.min(xarr), np.max(xarr))
            had = dict()
            for pl in sube.places():
                xpl = pl - offs
                reas = sube.getreason(pl)
                creas = rlookup[reas]
                if reas in had:
                    plt.axvline(xpl, color=creas, ls="--")
                else:
                    had[reas] = 1
                    plt.axvline(xpl, color=creas, label=reas, ls="--")
        if explicit_legend is not None:
            plt.legend([explicit_legend] + " (%d)" % fnum, handlelength=0)
        if outf is not None:
            fname = outf + ("_f%.3d.png" % fnum)
            f.savefig(fname)
        fnum += 1
else:
    lines = []
    if yrange is not None:
        plt.ylim(*yrange)
    if len(plotylab) == 0:
        plt.yticks([])
    else:
        if ytr:
            plt.gca().yaxis.tick_right()
            plt.gca().yaxis.set_label_position("right")
        plt.ylabel(plotylab)
    if len(xlab) == 0:
        plt.xticks([])
    else:
        if xtt:
            plt.gca().xaxis.tick_top()
            plt.gca().xaxis.set_label_position('top')
        plt.xlabel(xlab)

    for xarr, yarr, col in zip(rxarray,ryarray,colours):
        offs = xarr[0]
        xa = np.array(xarr) - offs
        ya = np.array(yarr)
        plt.plot(xa,ya, col)
        if excludes is not None:
            sube = elist.inrange(np.min(xarr), np.max(xarr))
            for pl in sube.places():
                xpl = pl - offs
                reas = sube.getreason(pl)
                creas = rlookup[reas]
                lines.append((xpl,creas))

    if explicit_legend is not None:
        plt.legend([explicit_legend], handlelength=0)

    for xpl, creas in lines:
        plt.axvline(xpl, color=creas, ls="--")
    if outf is not None:
        fname = outf + "_f.png"
        plt.savefig(fname)
        sys.exit(0)

# Only display pic if we're not saving

if forkoff:
    if os.fork() == 0:
        plt.show()
else:
    try:
        plt.show()
    except KeyboardInterrupt:
        pass
sys.exit(0)
