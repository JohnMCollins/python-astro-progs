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
import splittime
import periodarg

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
parsearg.add_argument('--sdplot', type=str, default='d', help='Action on separated plots, discontinuous/overlaid/separate')
parsearg.add_argument('--sepdays', type=float, default=1e6, help='Separate plots if this number of days apart')
parsearg.add_argument('--indaysep',type=str, default='1000d', help='Separate sections within day if this period apart')
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
parsearg.add_argument('--histcolour', type=str, default='blue,black', help='Colour or colour,colour for histogram and gauss')
parsearg.add_argument('--plotcolours', type=str, default='black,red,green,blue,yellow,magenta,cyan', help='Colours for successive plots')
parsearg.add_argument('--excludes', type=str, help='File with excluded obs times and reasons')
parsearg.add_argument('--exclcolours', type=str, default='red,green,blue,yellow,magenta,cyan,black', help='Colours for successive exclude reasons')

res = vars(parsearg.parse_args())
rf = res['integ'][0]
title = res['title']
dims = (res['width'], res['height'])
typeplot = res['type']
takelog = res['log']
sdp = res['sdplot']
sepdays = res['sepdays'] * periodarg.SECSPERDAY
try:
    indaysep = periodarg.periodarg(res['indaysep'])
except ValueError as e:
    print "Unknown sep period", res['indaysep']
    sys.exit(2)
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
histcolour = string.split(res['histcolour'], ',')
outf = res['outprefix']
excludes = res['excludes']

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

if inp.shape[0] < 8:
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
    datetimes = nowt + td(obsdates)
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

# Step one is to do the histogram

fig = plt.figure(figsize=dims)
fig.canvas.set_window_title(title + ' Histogram')

# If clipping histogram, iterate to remove outliers

hvals = vals.copy()

if clip != 0.0:
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

if histyrange is not None:
    plt.ylim(*histyrange)
if histxrange is not None:
    plt.xlim(*histxrange)

if gauss:
    histandgauss.histandgauss(hvals, bins=bins, colour=histcolour)
else:
    plt.hist(hvals, bins=bins, color=histcolour[0])

ax = plt.gca()

if ytr:
    ax.yaxis.tick_right()
    ax.yaxis.set_label_position("right")
if xtt:
    ax.xaxis.tick_top()
    ax.xaxis.set_label_position("top")
if len(histylab) > 0:
    plt.ylabel(histylab)
else:
    plt.yticks([])
if len(histxlab) > 0:
    if len(hvals) != len(vals):
        diff = len(vals) - len(hvals)
        if diff == 1: s=""
        else: s="s"
        histxlab += " (omitting %d outlying value%s)" % (diff, s)
    plt.xlabel(histxlab)
else:
    plt.xticks([])

# Save histogram output file if required

if outf is not None:
    fname = outf + '_hist.png'
    plt.savefig(fname)
if not sdp:
    fig = plt.figure(figsize=dims)
    fig.canvas.set_window_title(title + ' Value by time')

# Now for plot itself
# We use our split routine to split by date, splitting the jdates as well in case we're using those

separated_vals = splittime.splittime(sepdays, datetimes, obsdates, vals)

numplots = len(separated_vals)

plotcols = string.split(res['plotcolours'], ',')
colours = plotcols * ((numplots + len(plotcols) - 1) / len(plotcols))

fnum = 1

# Now do plot according to method chosen.

if len(sdp) == 0: sdp = 'd'

if sdp[0] == 's':
    
    # Case where we have each separate day plot in a different figure.
    
    for day_datetimes, day_jdates, day_values in separated_vals:
        
        colour = colours[fnum-1]
        fig = plt.figure(figsize=dims)
        fig.canvas.set_window_title(title + ' Day ' + str(fnum))
        if xrange is not None: plt.xlim(*xrange)        # Needs fixing for dates!!!!
        if yrange is not None: plt.ylim(*yrange)
        ax = plt.gca()
        if len(plotylab) == 0: plt.yticks([])
        else:
            if ytr:
                ax.yaxis.tick_right()
                ax.yaxis.set_label_position("right")
            plt.ylabel(plotylab)
        if len(xlab) == 0: plt.xticks([])
        else:
            if xtt:
                ax.xaxis.tick_top()
                ax.xaxis.set_label_position('top')
            plt.xlabel(xlab)
        subday_sep = splittime.splittime(indaysep, day_datetimes, day_jdates, day_values)
        if usedt:
            ax.xaxis.set_major_formatter(hfmt)
            fig.autofmt_xdate()
            for subday_datetimes, subday_jdates, subday_values in subday_sep:
                if len(subday_datetimes) != 0:
                    plt.plot(subday_datetimes, subday_values, colour)
        else:
            for subday_datetimes, subday_jdates, subday_values in subday_sep:
                if len(subday_datetimes) != 0:
                    plt.plot(subday_jdates, subday_values, colour)
        if excludes is not None:
            sube = elist.inrange(np.min(day_jdates), np.max(day_jdates))
            had = dict()
            leglist = []
            for pl in sube.places():
                reas = sube.getreason(pl)
                creas = rlookup[reas]
                xpl = pl
                if usedt: xpl = jdate.jdate_to_datetime(pl)
                if reas in had:
                    plt.axvline(xpl, color=creas, ls="--")
                else:
                    had[reas] = 1
                    (legl, ) = plt.axvline(xpl, color=creas, label=reas, ls="--")
                    leglist.append(legl)
            if len(leglist) > 0:
                legend(handles=leglist)
        if outf is not None:
            fname = outf + ("_f%.3d.png" % fnum)
            fig.savefig(fname)
        fnum += 1

elif sdp[0] == 'o':

    # Case where we overlay plots on top of each other
    # Thinks: maybe worry about different plots the same day?

    starting_datetime = separated_vals[0][0]
    #starting_dt_date = starting_datetime.date()
    starting_date = separated_vals[0][1]
    
    fig = plt.figure(figsize=dims)
    fig.canvas.set_window_title(title + ' all days')
        
    if xrange is not None: plt.xlim(*xrange)        # Needs fixing for dates!!!!
    if yrange is not None: plt.ylim(*yrange)
    ax = plt.gca()
    
    if usedt:
        ax.xaxis.set_major_formatter(hfmt)
        fig.autofmt_xdate()

    if len(plotylab) == 0: plt.yticks([])
    else:
        if ytr:
            ax.yaxis.tick_right()
            ax.yaxis.set_label_position("right")
        plt.ylabel(plotylab)
    if len(xlab) == 0: plt.xticks([])
    else:
        if xtt:
            ax.xaxis.tick_top()
            ax.xaxis.set_label_position('top')
        plt.xlabel(xlab)
    
    cnum = 0
    
    for day_datetimes, day_jdates, day_values in separated_vals:
        
        colour = colours[cnum]
        cnum += 1
        plotdts = [ datetime.datetime.combine(starting_date, day_dt.time()) for day_dt in day_datetimes ]
        subday_sep = splittime.splittime(indaysep, plotdts, day_jdates, day_values)
        if usedt:
            for subday_dts, subday_jdates, subday_values in subday_sep:
                if len(subday_dts) != 0:       
                    plt.plot(subday_dts, subday_values, colour)
        else:
            for subday_dts, subday_jdates, subday_values in subday_sep:
                if len(subday_dts) != 0:
                    plotjd = subday_jdates - day_jdates[0]
                    plt.plot(plotjd, subday_values, colour)
        
    # Don't worry about excludes for num
    
    if outf is not None:
        fname = outf + ("_f.png" % fnum)
        fig.savefig(fname)
    
else:
    
    colour = colours[0]
    
    fig = plt.figure(figsize=dims)
    fig.canvas.set_window_title(title + ' all days')
        
    if xrange is not None: plt.xlim(*xrange)        # Needs fixing for dates!!!!
    if yrange is not None: plt.ylim(*yrange)
    ax = plt.gca()
    
    if usedt:
        ax.xaxis.set_major_formatter(hfmt)
        fig.autofmt_xdate()

    if len(plotylab) == 0: plt.yticks([])
    else:
        if ytr:
            ax.yaxis.tick_right()
            ax.yaxis.set_label_position("right")
        plt.ylabel(plotylab)
    if len(xlab) == 0: plt.xticks([])
    else:
        if xtt:
            ax.xaxis.tick_top()
            ax.xaxis.set_label_position('top')
        plt.xlabel(xlab)
        
    for day_datetimes, day_jdates, day_values in separated_vals:      
        subday_sep = splittime.splittime(indaysep, day_datetimes, day_jdates, day_values)
        if usedt:
            for subday_datetimes, subday_jdates, subday_values in subday_sep:
                if len(subday_datetimes) != 0:
                    plt.plot(subday_datetimes, subday_values, colour)
        else:
            for subday_datetimes, subday_jdates, subday_values in subday_sep:
                if len(subday_datetimes) != 0:
                    plt.plot(subday_jdates, subday_values, colour)
    
    if excludes is not None:
        had = dict()
        leglist = []
        for pl in elist.places():
            reas = elist.getreason(pl)
            creas = rlookup[reas]
            xpl = pl
            if usedt: xpl = jdate.jdate_to_datetime(pl)
            if reas in had:
                plt.axvline(xpl, color=creas, ls="--")
            else:
                had[reas] = 1
                (legl, ) = plt.axvline(xpl, color=creas, label=reas, ls="--")
                leglist.append(legl)
        if len(leglist) > 0:
            legend(handles=leglist)
    
    if outf is not None:
        fname = outf + ("_f.png" % fnum)
        fig.savefig(fname)
        
# All done now either show figure or exit.

if outf is None:
    try:
        plt.show()
    except KeyboardInterrupt:
        pass

sys.exit(0)

