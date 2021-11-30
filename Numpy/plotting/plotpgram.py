#! /usr/bin/env python

import argparse
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
import numpy as np
import os.path
import os
import sys
import string
import rangearg
import argmaxmin
import warnings

warnings.simplefilter('error')

lstypes = dict(solid='-', dash='--', dot=':')

parsearg = argparse.ArgumentParser(description='Display chart of periods', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('spec', type=str, help='Spectrum file')
parsearg.add_argument('--title', help='Set window title', type=str, default="Periodogram display")
parsearg.add_argument('--outfig', type=str, help='Output figure')
parsearg.add_argument('--colour', type=str, default='blue', help='Line colour')
parsearg.add_argument('--maxnum', type=int, default=0, help='Number of maxima to take')
parsearg.add_argument('--maxcol', type=str, default='green', help='Colour of lines denoting maxima')
parsearg.add_argument('--mtxtcol', type=str, help='Colour of text denoting maxima if not same as lines')
parsearg.add_argument('--rottxt', type=float, default=45, help='Rotation of text')
parsearg.add_argument('--mxoffs', type=float, default=2.0, help='Offset of maxima line labels X (percent) -ve for LHS of line')
parsearg.add_argument('--myoffs', type=str, default='10.0', help='Offset of maxima line labels Y (percent)')
parsearg.add_argument('--mxprec', type=int, default=1, help='Precision of maxima labels')
parsearg.add_argument('--addinten', action='store_true', help='Put amplitudes on line labels')
parsearg.add_argument('--xlab', type=str, help='Label for X axis', default='Period in days')
parsearg.add_argument('--ylab', type=str, help='Label for Y axis', default='Power')
parsearg.add_argument('--yaxr', action='store_true', help='Put Y axis label on right')
parsearg.add_argument('--yrange', type=str, help='Range for Y axis')
parsearg.add_argument('--xaxt', action='store_true', help='Put X axis label on top')
parsearg.add_argument('--xrange', type=str, help='Range for X axis')
parsearg.add_argument('--mxxrange', type=str, help='Range of X axis for considering maxima')
parsearg.add_argument('--xtickint', type=float, help='Tick interval X xavis')
parsearg.add_argument('--fork', action='store_true', help='Fork off daemon process to show plot and exit')
parsearg.add_argument('--legend', type=str, help='Specify legend')
parsearg.add_argument('--legloc', type=str, default='best', help='Location for legend')
parsearg.add_argument('--width', help="Width of plot", type=float, default=8)
parsearg.add_argument('--height', help="Height of plot", type=float, default=6)
parsearg.add_argument('--logscale', action='store_true', help='Show X axis in log scale')
parsearg.add_argument('--faps', type=int, nargs='+', help='PAP lines to show')
parsearg.add_argument('--fapc', type=str, default='k', help='FAP line colour')
parsearg.add_argument('--fapls', type=str, default='dot', help='FAP line style')
parsearg.add_argument('--fapx', type=float, help='Offset from lh for FAP text')
parsearg.add_argument('--fapy', type=float, help='Offset from line from FAP text')
parsearg.add_argument('--fapprec', type=int, default=3, help='Precision for FAP value')
parsearg.add_argument('--textfs', type=int, default=10, help='Plot text font size')
parsearg.add_argument('--recip', type=str, help='input is frequency take recip c=cycles/day a=angular (2pi/fred)')

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
mxxrange = rangearg.parserange(resargs['mxxrange'])
if mxxrange is None: mxxrange = xrange
exlegend = resargs['legend']
legloc = resargs['legloc']
recip = resargs['recip']

faps = resargs['faps']
if faps is None: faps = []
fapc = resargs['fapc']
fapls = lstypes[resargs['fapls']]
fapx = resargs['fapx']
fapy = resargs['fapy']
fapprec = resargs['fapprec']
fapfmt= 'FAP=%%#.%dg' % fapprec
textfs = resargs['textfs']

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
fig.canvas.manager.set_window_title(resargs['title'])

try:
    f = np.loadtxt(spec, unpack=True)
    periods = f[0]
    amps = f[1]
    if recip is not None:
        if recip == 'c':
            periods = 1.0 / periods
        elif recip == 'a':
            periods = np.pi * 2.0 / periods
        else:
            print "Cannot understand recip arg should be c or a not", recip
            sys.exit(9)
    if len(faps) != 0:
        fapvalues = f[2]
    else:
        fapvalues = np.ones_like(amps)
except IOError as e:
    print "Could not load spectrum file", spec, "error was", e.args[1]
    sys.exit(11)
except ValueError:
    print "Conversion error on", spec
    sys.exit(12)
except IndexError:
    print "File of wrong shape"
    if faps is not None:
        print "No FAPs"
        sys.exit(13)

    
col=resargs['colour']
lscale = resargs['logscale']
xtickint = resargs['xtickint']

ax = plt.gca()
if lscale:
	ax.set_xscale('log')
	ax.get_xaxis().set_major_formatter(ScalarFormatter())
if xrange is not None:
    plt.xlim(*xrange)
if yrange is not None:
    plt.ylim(*yrange)
plt.plot(periods, amps, color=col)
xrange = ax.get_xlim()
yrange = ax.get_ylim()
xticks = None
if xtickint is not None:
    xticks = np.arange(xrange[0], xrange[1]+xtickint, xtickint)
if len(ylab) == 0:
    plt.yticks([])
else:
    if ytr:
        ax.yaxis.tick_right()
        ax.yaxis.set_label_position("right")
    plt.ylabel(ylab, fontsize=textfs)
if len(xlab) == 0:
    plt.xticks([])
else:
    if xticks is not None:
        plt.xticks(xticks)
    if xtt:
        ax.xaxis.tick_top()
        ax.xaxis.set_label_position('top')
    plt.xlabel(xlab, fontsize=textfs)
if exlegend is not None:
    leg = plt.legend([exlegend], handlelength=0, handletextpad=0, fancybox=True, loc=legloc)
    for l in leg.legendHandles:
        l.set_visible(False)

addinten = resargs['addinten']
maxnum = resargs['maxnum']

if maxnum > 0:
    myoffs = [float(x) for x in string.split(string.replace(resargs['myoffs'], ':', ','), ',')]
    if len(myoffs) < maxnum:
        myoffs *= maxnum
    mcol = resargs['maxcol']
    mrot = resargs['rottxt']
    mtxtcol = resargs['mtxtcol']
    if mtxtcol is None: mtxtcol = mcol
    mcol = string.split(mcol, ',') * maxnum
    mtxtcol = string.split(mtxtcol, ',') * maxnum
    if mxxrange is not None:
        selx = (periods >= mxxrange[0]) & (periods <= mxxrange[1])
        periods = periods[selx]
        amps = amps[selx]
        fapvalues = fapvalues[selx]
    maxima = argmaxmin.maxmaxes(periods, amps)
    # If that's too many, prune taking the largest
    if len(maxima) > maxnum: maxima = maxima[0:maxnum]
    xoffssc = resargs['mxoffs'] / 100.0
    xoffs = (xrange[1] - xrange[0]) * xoffssc
    xscale = 1 + xoffssc
    mprec = resargs['mxprec']
    mprec = "%%.%df" % mprec

    for n, m in enumerate(maxima):
        maxx = periods[m]
        maxy = amps[m]
        maxfap = fapvalues[m]
        plt.axvline(maxx, color=mcol[n])
        if lscale:
	        xplace = maxx*xscale
        else:
			xplace = maxx+xoffs
        yoffssc = myoffs[n] / 100.0
        yplace = np.dot(yrange, (yoffssc, 1-yoffssc))
        if xrange[0] < xplace < xrange[1]:
            if addinten:
                plt.text(xplace, yplace, (mprec + ',' + '%#.3g') % (maxx, maxy), color=mtxtcol[n], rotation=mrot, fontsize=textfs)
            else:
                plt.text(xplace, yplace, mprec % maxx, color=mtxtcol[n], rotation=mrot, fontsize=textfs)
        if n+1 in faps:
            if fapx is None:
                mnx, mxx = plt.gca().get_xlim()
                fapx = mnx + .9 * (mxx-mnx)
            if fapy is None:
                mny, mxy = plt.gca().get_ylim()
                fapy = .1 * (mxy-mny) 
            plt.axhline(maxy, color=fapc, linestyle=fapls)
            plt.text(fapx, maxy+fapy, fapfmt % maxfap, color=fapc, fontsize=textfs)

plt.tight_layout()
if outfig is not None:
    plt.savefig(outfig)
    sys.exit(0)
if not forkoff or os.fork() == 0:
    try:
        plt.show()
    except KeyboardInterrupt:
        pass
