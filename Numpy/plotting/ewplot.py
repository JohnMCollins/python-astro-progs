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

parsearg = argparse.ArgumentParser(description='Plot equivalent width results', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('integ', type=str, nargs=1, help='Input integration file (time/intensity)')
parsearg.add_argument('--title', type=str, default='Equivalent widths', help='Title for window')
parsearg.add_argument('--width', type=float, default=8, help='Display width')
parsearg.add_argument('--height', type=float, default=6, help='Display height')
parsearg.add_argument('--type', help='ew/ps/pr to select display', type=str, default="ew")
parsearg.add_argument('--log', action='store_true', help='Take log of values to plot')
parsearg.add_argument('--sdplot', type=str, default='d', help='Action on separated plots, discontinuous/overlaid/separate')
parsearg.add_argument('--sepdays', type=float, default=1e6, help='Separate plots if this number of days apart')
parsearg.add_argument('--indaysep',type=str, default='1000d', help='Separate sections within day if this period apart')
parsearg.add_argument('--bins', type=int, default=20, help='Histogram bins')
parsearg.add_argument('--clip', type=float, default=0.0, help='Number of S.D.s to clip from histogram')
parsearg.add_argument('--gauss', action='store_true', help='Normalise and overlay gaussian on histogram')
parsearg.add_argument('--xtype', type=str, default='auto', help='Type X axis - time/date/full/days')
parsearg.add_argument('--daterot', type=float, default=30.0, help='Rotataion for dates on X axis')
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
parsearg.add_argument('--scatter', action='store_true', help='Do scatter plot rather than plot')
parsearg.add_argument('--excludes', type=str, help='File with excluded obs times and reasons')
parsearg.add_argument('--exclcolours', type=str, default='red,green,blue,yellow,magenta,cyan,black', help='Colours for successive exclude reasons')

resargs = vars(parsearg.parse_args())
rf = resargs['integ'][0]
title = resargs['title']
dims = (resargs['width'], resargs['height'])
typeplot = resargs['type']
takelog = resargs['log']
sdp = resargs['sdplot']
sepdays = resargs['sepdays'] * periodarg.SECSPERDAY
try:
    indaysep = periodarg.periodarg(resargs['indaysep'])
except ValueError as e:
    print "Unknown sep period", resargs['indaysep']
    sys.exit(2)
bins = resargs['bins']
clip = resargs['clip']
gauss = resargs['gauss']
xtype = resargs['xtype']
drot = resargs['daterot']
xtt = resargs['xaxt']
ytr = resargs['yaxr']
xrange = rangearg.parserange(resargs['xrange'])
yrange = rangearg.parserange(resargs['yrange'])
histxrange = rangearg.parserange(resargs['histxrange'])
histyrange = rangearg.parserange(resargs['histyrange'])
histcolour = string.split(resargs['histcolour'], ',')
outf = resargs['outprefix']
excludes = resargs['excludes']

plotting_function = plt.plot
if resargs['scatter']: plotting_function = plt.scatter

if typeplot not in optdict:
    print "Unknown type", typeplot, "specified"
    sys.exit(2)
ycolumn, histxlab, plotylab = optdict[typeplot]
if resargs['xhist'] is not None:
    histxlab = resargs['xhist']
    if histxlab == "none":
        histxlab = ""
if resargs['yplot'] is not None:
    plotylab = resargs['yplot']
    if plotylab == "none":
        ylab = ""

# Ones not dependent on column

histylab = resargs['yhist']
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
    excols = string.split(resargs['exclcolours'], ',')
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
    if takelog:
        bins = np.logspace(*np.log10(histxrange), num=bins)
    else:
        bins = np.linspace(*histxrange, num=bins)

ax = plt.gca()
ax.get_xaxis().get_major_formatter().set_useOffset(False)
if takelog:
    ax.set_xscale('log')

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

fig.tight_layout()
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

plotcols = string.split(resargs['plotcolours'], ',')
colours = plotcols * ((numplots + len(plotcols) - 1) / len(plotcols))

fnum = 1

# Now do plot according to method chosen.

if len(sdp) == 0: sdp = 'd'

if sdp[0] == 's':
    
    # Case where we have each separate day plot in a different figure.
    
    for day_datetimes, day_jdates, day_values in separated_vals:
        
        if len(day_datetimes) < 2:
            continue
        
        colour = colours[fnum-1]
        fig = plt.figure(figsize=dims)
        fig.canvas.set_window_title(title + ' Day ' + str(fnum))
        if xrange is not None: plt.xlim(*xrange)        # Needs fixing for dates!!!!
        if yrange is not None: plt.ylim(*yrange)
        ax = plt.gca()
        ax.get_yaxis().get_major_formatter().set_useOffset(False)
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
        if len(day_datetimes) > 10:
            subday_sep = splittime.splittime(indaysep, day_datetimes, day_jdates, day_values)
        else:
            subday_sep = ((day_datetimes, day_jdates, day_values), )
        if usedt:
            ax.xaxis.set_major_formatter(hfmt)
            fig.autofmt_xdate(rotation=drot)
            for subday_datetimes, subday_jdates, subday_values in subday_sep:
                if len(subday_datetimes) != 0:
                    plotting_function(subday_datetimes, subday_values, color=colour)
        else:
            for subday_datetimes, subday_jdates, subday_values in subday_sep:
                if len(subday_datetimes) != 0:
                    plotting_function(subday_jdates, subday_values, color=colour)
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
        fig.tight_layout()
        if outf is not None:
            fname = outf + ("_f%.3d.png" % fnum)
            fig.savefig(fname)
        fnum += 1

elif sdp[0] == 'o':

    # Case where we overlay plots on top of each other
    # Thinks: maybe worry about different plots the same day?

    starting_datetime = separated_vals[0][0][0]
    starting_date = starting_datetime.date()
    
    fig = plt.figure(figsize=dims)
    fig.canvas.set_window_title(title + ' all days')
        
    if xrange is not None: plt.xlim(*xrange)        # Needs fixing for dates!!!!
    if yrange is not None: plt.ylim(*yrange)
    ax = plt.gca()
    ax.get_yaxis().get_major_formatter().set_useOffset(False)
    
    if usedt:
        ax.xaxis.set_major_formatter(hfmt)
        fig.autofmt_xdate(rotation=drot)

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
        
        if len(day_datetimes) < 2:
            continue

        colour = colours[cnum]
        cnum += 1
        plotdts = []
        # rethink this
        plotdts = [ datetime.datetime.combine(starting_date, day_dt.time()) for day_dt in day_datetimes ]
        if len(day_datetimes) > 10:
            subday_sep = splittime.splittime(indaysep, plotdts, day_jdates, day_values)
        else:
            subday_sep = ((plotdts, day_jdates, day_values), )
        if usedt:
            for subday_dts, subday_jdates, subday_values in subday_sep:
                if len(subday_dts) != 0:       
                    plotting_function(subday_dts, subday_values, color=colour)
        else:
            for subday_dts, subday_jdates, subday_values in subday_sep:
                if len(subday_dts) != 0:
                    plotjd = subday_jdates - day_jdates[0]
                    plotting_function(plotjd, subday_values, color=colour)
        
    # Don't worry about excludes for num
    
    fig.tight_layout()
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
    ax.get_yaxis().get_major_formatter().set_useOffset(False)
    
    if usedt:
        ax.xaxis.set_major_formatter(hfmt)
        fig.autofmt_xdate(rotation=drot)

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
        
        if len(day_datetimes) < 2:
            continue

        if len(day_datetimes) > 10:
            subday_sep = splittime.splittime(indaysep, day_datetimes, day_jdates, day_values)
        else:
            subday_sep = ((day_datetimes, day_jdates, day_values),)
        if usedt:
            for subday_datetimes, subday_jdates, subday_values in subday_sep:
                if len(subday_datetimes) != 0:
                    plotting_function(subday_datetimes, subday_values, color=colour)
        else:
            for subday_datetimes, subday_jdates, subday_values in subday_sep:
                if len(subday_datetimes) != 0:
                    plotting_function(subday_jdates, subday_values, color=colour)
    
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
    
    fig.tight_layout()
    if outf is not None:
        fname = outf + "_f.png"
        fig.savefig(fname)
        
# All done now either show figure or exit.

if outf is None:
    try:
        plt.show()
    except KeyboardInterrupt:
        pass

sys.exit(0)
