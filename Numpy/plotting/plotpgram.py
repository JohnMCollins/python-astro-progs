#! /usr/bin/env python

import argparse
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
import scipy.signal as ss
import numpy as np
import os.path
import os
import sys
import string
import rangearg
import argmaxmin

parsearg = argparse.ArgumentParser(description='Display chart of periods')
parsearg.add_argument('spec', type=str, help='Spectrum file')
parsearg.add_argument('--title', help='Set window title', type=str, default="Periodogram display")
parsearg.add_argument('--outfig', type=str, help='Output figure')
parsearg.add_argument('--colour', type=str, default='blue', help='Line colour')
parsearg.add_argument('--maxnum', type=int, default=0, help='Number of maxima to take')
parsearg.add_argument('--maxcol', type=str, default='green', help='Colour of lines denoting maxima')
parsearg.add_argument('--mtxtcol', type=str, help='Colour of text denoting maxima if not same as lines')
parsearg.add_argument('--rottxt', type=float, default=45, help='Rotation of text')
parsearg.add_argument('--mxoffs', type=float, default=2.0, help='Offset of maxima line labels X (percent) -ve for LHS of line')
parsearg.add_argument('--myoffs', type=float, default=10.0, help='Offset of maxima line labels Y (percent)')
parsearg.add_argument('--addinten', action='store_true', help='Put amplitudes on line labels')
parsearg.add_argument('--xlab', type=str, help='Label for X axis', default='Period in days')
parsearg.add_argument('--ylab', type=str, help='Label for Y axis', default='Amplitude of signal')
parsearg.add_argument('--yaxr', action='store_true', help='Put Y axis label on right')
parsearg.add_argument('--yrange', type=str, help='Range for Y axis')
parsearg.add_argument('--xaxt', action='store_true', help='Put X axis label on top')
parsearg.add_argument('--xrange', type=str, help='Range for X axis')
parsearg.add_argument('--fork', action='store_true', help='Fork off daemon process to show plot and exit')
parsearg.add_argument('--legend', type=str, help='Specify legend')
parsearg.add_argument('--width', help="Width of plot", type=float, default=8)
parsearg.add_argument('--height', help="Height of plot", type=float, default=6)
parsearg.add_argument('--logscale', action='store_true', help='Show X axis in log scale')

resargs = vars(parsearg.parse_args())

spec = resargs['spec']
outfig = resargs['outfig']
xlab = resargs['xlab']
ylab = resargs['ylab']
if xlab == "none":
    xlab = ""
if ylab == "none":
    ylab = ""
ytr = resargs['yaxr']
xtt = resargs['xaxt']
yrange = rangearg.parserange(resargs['yrange'])
xrange = rangearg.parserange(resargs['xrange'])
exlegend = resargs['legend']

forkoff = resargs['fork']

errors = 0

if spec is None or not os.path.isfile(spec):
    print "No spectrum file"
    errors += 1
    spec = "none"

width = resargs['width']
if width <= 0:
    print "Cannot have -ve or zero width"
    errors += 1

plt.rcParams['figure.figsize'] = (width, resargs['height'])

fig = plt.gcf()
fig.canvas.set_window_title(resargs['title'])

try:
    periods, amps = np.loadtxt(spec, unpack=True)
except IOError as e:
    print "Could not load spectrum file", spec, "error was", e.args[1]
    sys.exit(11)
except ValueError:
    print "Conversion error on", spec
    sys.exit(12)

col=resargs['colour']
lscale = resargs['logscale']

ax = plt.gca()
if lscale:
	ax.set_xscale('log')
	ax.xaxis.set_major_formatter(ScalarFormatter())
if xrange is not None:
    plt.xlim(*xrange)
if yrange is not None:
    plt.ylim(*yrange)
plt.plot(periods, amps, color=col)
xrange = ax.get_xlim()
yrange = ax.get_ylim()
if len(ylab) == 0:
    plt.yticks([])
else:
    if ytr:
        ax.yaxis.tick_right()
        ax.yaxis.set_label_position("right")
    plt.ylabel(ylab)
if len(xlab) == 0:
    plt.xticks([])
else:
    if xtt:
        ax.xaxis.tick_top()
        ax.xaxis.set_label_position('top')
    plt.xlabel(xlab)
if exlegend is not None:
    plt.legend([exlegend], handlelength=0)

addinten = resargs['addinten']
maxnum = resargs['maxnum']
if maxnum > 0:
    mcol = resargs['maxcol']
    mrot = resargs['rottxt']
    mtxtcol = resargs['mtxtcol']
    if mtxtcol is None: mtxtcol = mcol
    mcol = string.split(mcol, ',') * maxnum
    mtxtcol = string.split(mtxtcol, ',') * maxnum
    if xrange is not None:
        selx = (periods >= xrange[0]) & (periods <= xrange[1])
        periods = periods[selx]
        amps = amps[selx]
    maxima = argmaxmin.maxmaxes(periods, amps)
    # If that's too many, prune taking the largest
    if len(maxima) > maxnum: maxima = maxima[0:maxnum]
    yoffssc = resargs['myoffs'] / 100.0
    yplace = np.dot(yrange, (yoffssc, 1-yoffssc))
    xoffssc = resargs['mxoffs'] / 100.0
    xoffs = (xrange[1] - xrange[0]) * xoffssc
    xscale = 1 + xoffssc

    for n, m in enumerate(maxima):
        maxx = periods[m]
        maxy = amps[m]
        plt.axvline(maxx, color=mcol[n])
        if lscale:
	        xplace = maxx*xscale
        else:
			xplace = maxx+xoffs
        if xrange[0] < xplace < xrange[1]:
            if addinten:
                plt.text(xplace, yplace, "%#.4g, %#.4g" % (maxx, maxy), color=mtxtcol[n], rotation=mrot)
            else:
                plt.text(xplace, yplace, "%#.4g" % maxx, color=mtxtcol[n], rotation=mrot)

if outfig is not None:
    plt.savefig(outfig)
    sys.exit(0)
if not forkoff or os.fork() == 0:
    try:
        plt.show()
    except KeyboardInterrupt:
        pass

