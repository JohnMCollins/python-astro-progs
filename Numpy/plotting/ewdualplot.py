#! /usr/bin/env python

# Dual plot of alternative EWs

import argparse
import os.path
import sys
import string
import numpy as np
import scipy.stats as ss
import matplotlib.pyplot as plt
from matplotlib import dates
import datetime
import jdate
import rangearg
import splittime
import periodarg

parsearg = argparse.ArgumentParser(description='Plot parallel equivalent width results', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('integ', type=str, nargs=2, help='Input EW files')
parsearg.add_argument('--title', type=str, default='Equivalent widths', help='Title for window')
parsearg.add_argument('--width', type=float, default=8, help='Display width')
parsearg.add_argument('--height', type=float, default=6, help='Display height')
parsearg.add_argument('--log', action='store_true', help='Take log of values to plot')
parsearg.add_argument('--sepdays', type=float, default=1e6, help='Separate plots if this number of days apart')
parsearg.add_argument('--indaysep',type=str, default='1000d', help='Separate sections within day if this period apart')
parsearg.add_argument('--xtype', type=str, default='auto', help='Type X axis - time/date/full/days')
parsearg.add_argument('--daterot', type=float, default=30.0, help='Rotataion for dates on X axis')
parsearg.add_argument('--xplot', type=str, help='Label for plot X axis')
parsearg.add_argument('--yplot', type=str, help='Label for plot Y axis')
parsearg.add_argument('--xrange', type=str, help='Range for X axis')
parsearg.add_argument('--y1range', type=str, help='Range for Y 1 axis')
parsearg.add_argument('--y2range', type=str, help='Range for Y 2 axis')
parsearg.add_argument('--y1ticks', type=float, help='Tick interval y1')
parsearg.add_argument('--y2ticks', type=float, help='Tick interval y2')
parsearg.add_argument('--outprefix', type=str, help='Output file prefix')
parsearg.add_argument('--plotcolours', type=str, default='k,b', help='Colours for successive plots')
parsearg.add_argument('--scatter', action='store_true', help='Do scatter plot rather than plot')

resargs = vars(parsearg.parse_args())
rf = resargs['integ']
title = resargs['title']
dims = (resargs['width'], resargs['height'])
takelog = resargs['log']
sepdays = resargs['sepdays'] * periodarg.SECSPERDAY
try:
    indaysep = periodarg.periodarg(resargs['indaysep'])
except ValueError as e:
    print "Unknown sep period", resargs['indaysep']
    sys.exit(2)
xtype = resargs['xtype']
drot = resargs['daterot']
xrange = rangearg.parserange(resargs['xrange'])
y1range = rangearg.parserange(resargs['y1range'])
y2range = rangearg.parserange(resargs['y2range'])
y1ticks = resargs['y1ticks']
y2ticks = resargs['y2ticks']
outf = resargs['outprefix']

plotting_function = plt.plot
if resargs['scatter']: plotting_function = plt.scatter

if resargs['yplot'] is not None:
    plotylab = resargs['yplot']
    if plotylab == "none":
        ylab = ""
else:
    plotylab = "Equivalent Width ($\AA$)"

# Load up EW files

try:
    inp1 = np.loadtxt(rf[0], unpack=True)
except IOError as e:
    print "Error loading EW file", rf[0]
    print "Error was", e.args[1]
    sys.exit(102)

try:
    inp2 = np.loadtxt(rf[1], unpack=True)
except IOError as e:
    print "Error loading EW file", rf[1]
    print "Error was", e.args[1]
    sys.exit(103)

if inp1.shape[0] < 8 or inp2.shape[0] < 8:
    print "Expecting new format 8-column shape, please convert"
    print "Shapes was", inp1.shape, "and", inp2.shape
    sys.exit(104)

obsdates = inp1[0]
if np.count_nonzero(obsdates != inp2[0]) != 0:
    print "File dates to not line up"
    sys.exit(105)

ews1 = inp1[2]
ews2 = inp2[2]

if takelog and (np.min(ews1) < 0 or np.min(ews2) < 0):
    print "Negative values, cannot take log"
    sys.exit(106)

# If first element is zero, make dates as offset from "now"

if obsdates[0] == 0.0:
    nowt = datetime.datetime.now()
    td = np.vectorize(datetime.timedelta)
    datetimes = nowt + td(obsdates)
    sim = "(Simulated) "
else:
    td = np.vectorize(jdate.jdate_to_datetime)
    datetimes = td(obsdates)
    sim = ""

xlab = resargs['xplot']

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

# Now for plot itself
# We use our split routine to split by date, splitting the jdates as well in case we're using those

separated_vals = splittime.splittime(sepdays, datetimes, obsdates, ews1, ews2)

numplots = len(separated_vals)

plotcols = string.split(resargs['plotcolours'], ',')
if len(plotcols) < 2:
    print "Expecting at least 2 plot colours"
    sys.exit(107)

fnum = 1
for day_datetimes, day_jdates, day_ew1, day_ew2 in separated_vals:
    if len(day_datetimes) < 2:
        continue
    fig = plt.figure(figsize=dims)
    fig.canvas.manager.set_window_title(title + ' period ' + str(fnum))
    if xrange is not None: plt.xlim(*xrange)
    if y1range is not None: plt.ylim(*y1range)
    ax = plt.gca()
    if takelog:
        ax.set_yscale('log')
    if y1range is not None and y1ticks is not None:
        ax.set_yticks(np.arange(y1range[0], y1range[1], y1ticks))
    elif not takelog:
        ax.get_yaxis().get_major_formatter().set_useOffset(False)
    if len(plotylab) != 0:
        plt.ylabel(plotylab, color=plotcols[0])
    if len(xlab) == 0:
        plt.xticks([])
    else:
        plt.xlabel(xlab)
    if len(day_datetimes) > 10:
        subday_sep = splittime.splittime(indaysep, day_datetimes, day_jdates, day_ew1, day_ew2)
    else:
        subday_sep = ((day_datetimes, day_jdates, day_ew1, day_ew2), )
    if usedt:
        ax.xaxis.set_major_formatter(hfmt)
    fig.autofmt_xdate(rotation=drot)
    for subday_datetimes, subday_jdates, subday_ew1, subday_ew2 in subday_sep:
        if len(subday_datetimes) != 0:
            plotting_function(subday_datetimes, subday_ew1, color=plotcols[0])
        else:
            for subday_datetimes, subday_jdates, subday_ew1, subday_ew2 in subday_sep:
                if len(subday_datetimes) != 0:
                    plotting_function(subday_jdates, subday_ew1, color=plotcols[0])
    ax = plt.twinx(ax)
    if y2range is not None: plt.ylim(*y2range)
    if takelog:
        ax.set_yscale('log')
    if y2range is not None and y2ticks is not None:
        ax.set_yticks(np.arange(y2range[0], y2range[1], y2ticks))
    elif not takelog:
        ax.get_yaxis().get_major_formatter().set_useOffset(False)
    if len(plotylab) != 0:
        plt.ylabel(plotylab, color=plotcols[1])
    for subday_datetimes, subday_jdates, subday_ew1, subday_ew2 in subday_sep:
        if len(subday_datetimes) != 0:
            plotting_function(subday_datetimes, subday_ew2, color=plotcols[1])
        else:
            for subday_datetimes, subday_jdates, subday_ew1, subday_ew2 in subday_sep:
                if len(subday_datetimes) != 0:
                    plotting_function(subday_jdates, subday_ew2, color=plotcols[1])
    fig.tight_layout()
    if outf is not None:
        fname = outf + ("_f%.3d.png" % fnum)
        fig.savefig(fname)
    fnum += 1

# All done now either show figure or exit.

if outf is None:
    try:
        plt.show()
    except KeyboardInterrupt:
        pass

sys.exit(0)
