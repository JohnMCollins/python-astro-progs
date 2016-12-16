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

def plot_with_maxima(periods, amps, xrng, yrng, ylab):
    """Plot subplot from given periods/amps/range/label"""
    global textfs, plotcolour, maxnum, mxxrange, mcol, xoffsc, myoffs, addinten, mprec, mtxtcol, mrot

    if xrng is not None:
        plt.xlim(*xrng)
    if yrng is not None:
        plt.ylim(*yrng)
    if len(ylab) == 0:
        plt.yticks([])
    else:
        plt.ylabel(ylab, fontsize=textfs)

    plt.plot(periods, amps, color=plotcolour)
    
    if maxnum <= 0:
        return
        
    if mxxrange is not None:
        selx = (periods >= mxxrange[0]) & (periods <= mxxrange[1])
        periods = periods[selx]
        amps = amps[selx]
    
    maxima = argmaxmin.maxmaxes(periods, amps)
    
    # If that's too many, prune taking the largest
    
    if len(maxima) > maxnum: maxima = maxima[0:maxnum]
    
    xrange = plt.gca().get_xlim()
    yrange = plt.gca().get_ylim()
    
    for n, m in enumerate(maxima):
        maxx = periods[m]
        maxy = amps[m]
        plt.axvline(maxx, color=mcol[n])
        xoffs = (xrange[1] - xrange[0]) * xoffssc
        xscale = 1 + xoffssc
        xplace = maxx + xoffs
        yoffssc = myoffs[n] / 100.0
        yplace = np.dot(yrange, (yoffssc, 1-yoffssc))
        
        if xrange[0] < xplace < xrange[1]:
            if addinten:
                plt.text(xplace, yplace, (mprec + ',' + '%#.3g') % (maxx, maxy), color=mtxtcol[n], rotation=mrot, fontsize=textfs)
            else:
                plt.text(xplace, yplace, mprec % maxx, color=mtxtcol[n], rotation=mrot, fontsize=textfs)


## Main starts here

parsearg = argparse.ArgumentParser(description='Plot results from Period 04', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('pfiles', nargs=2, type=str, help='Period 04 files, pgram winfunc')
parsearg.add_argument('--title', help='Set window title', type=str, default="Period 04 results display")
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
parsearg.add_argument('--y1lab', type=str, help='Label for Y1 axis', default='Power')
parsearg.add_argument('--y2lab', type=str, help='Label for Y2 axis', default='Power')
parsearg.add_argument('--y1range', type=str, help='Range for Y1 axis')
parsearg.add_argument('--y2range', type=str, help='Range for Y2 axis')
parsearg.add_argument('--xrange', type=str, help='Range for X axis')
parsearg.add_argument('--mxxrange', type=str, help='Range of X axis for considering maxima')
parsearg.add_argument('--xtickint', type=float, help='Tick interval X xavis')
parsearg.add_argument('--legend', type=str, help='Specify legend')
parsearg.add_argument('--legloc', type=str, default='best', help='Location for legend')
parsearg.add_argument('--width', help="Width of plot", type=float, default=8)
parsearg.add_argument('--height', help="Height of plot", type=float, default=6)
parsearg.add_argument('--textfs', type=int, default=10, help='Plot text font size')

resargs = vars(parsearg.parse_args())

pgramfile, winfuncfile = resargs['pfiles']
outfig = resargs['outfig']
xlab = resargs['xlab']
y1lab = resargs['y1lab']
y2lab = resargs['y2lab']
if xlab == "none":
    xlab = ""
if y1lab == "none":
    y1lab = ""
if y2lab == "none":
    y2lab = ""
y1range = rangearg.parserange(resargs['y1range'])
y2range = rangearg.parserange(resargs['y2range'])
xrange = rangearg.parserange(resargs['xrange'])
mxxrange = rangearg.parserange(resargs['mxxrange'])
if mxxrange is None: mxxrange = xrange
exlegend = resargs['legend']
legloc = resargs['legloc']
textfs = resargs['textfs']

try:
    pfreq, pamp = np.loadtxt(pgramfile, unpack=True)
    if pfreq[0] == 0:
        pfreq = pfreq[1:]
        pam = pamp[1:]
    per = 1.0 / pfreq
except IOError as e:
    print "Could not load pgram file", pgramfile, "error was", e.args[1]
    sys.exit(11)
except ValueError:
    print "File", pgramfile, "of wrong shape"
    sys.exit(12)

try:
    wfreq, wamp = np.loadtxt(winfuncfile, unpack=True)
    if wfreq[0] == 0:
        wfreq = wfreq[1:]
        wam = wamp[1:]
    wer = 1.0 / wfreq
except IOError as e:
    print "Could not load winfunc file", winfuncfile, "error was", e.args[1]
    sys.exit(11)
except ValueError:
    print "File", winfuncfile, "of wrong shape"
    sys.exit(12)
    
plotcolour = resargs['colour']
xtickint = resargs['xtickint']
addinten = resargs['addinten']

# Get arg stuff for maxima

maxnum = resargs['maxnum']
mcol = resargs['maxcol']
mrot = resargs['rottxt']
mtxtcol = resargs['mtxtcol']
if mtxtcol is None: mtxtcol = mcol
mcol = string.split(mcol, ',') * maxnum
mtxtcol = string.split(mtxtcol, ',') * maxnum
myoffs = [float(x) for x in string.split(string.replace(resargs['myoffs'], ':', ','), ',')]
if len(myoffs) < maxnum:
    myoffs *= maxnum
xoffssc = resargs['mxoffs'] / 100.0
mprec = resargs['mxprec']
mprec = "%%.%df" % mprec

# OK let's get on with it

plt.rcParams['figure.figsize'] = (resargs['width'], resargs['height'])
fig = plt.gcf()
fig.canvas.set_window_title(resargs['title'])

if xrange is not None:
    plt.xlim(*xrange)

ax1 = plt.subplot(2, 1, 1)
plot_with_maxima(per, pam, xrange, y1range, y1lab)
ax2 = plt.subplot(2, 1, 2, sharex=ax1)
plot_with_maxima(wer, wam, xrange, y2range, y2lab)

xrange = ax1.get_xlim()
xticks = None
if xtickint is not None:
    xticks = np.arange(xrange[0], xrange[1]+xtickint, xtickint)
if len(xlab) == 0:
    plt.xticks([])
else:
    if xticks is not None:
        plt.xticks(xticks)
    plt.xlabel(xlab, fontsize=textfs)
if exlegend is not None:
    leg = plt.legend([exlegend], handlelength=0, handletextpad=0, fancybox=True, loc=legloc)
    for l in leg.legendHandles:
        l.set_visible(False)

plt.tight_layout()
plt.subplots_adjust(hspace = 0)
if outfig is not None:
    plt.savefig(outfig)
    sys.exit(0)
plt.show()
