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

optdict = dict(ew = (2, 'Equivalent width ($\AA$)'),
               ps = (4, 'Peak size (rel to EW)'),
               pr = (6, 'Peak ratio'))

parsearg = argparse.ArgumentParser(description='Plot comparative EW histograms', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('integ', type=str, nargs='+', help='Input integration files (time/intensity)')
parsearg.add_argument('--title', type=str, default='Equivalent widths', help='Title for window')
parsearg.add_argument('--width', type=float, default=8, help='Display width')
parsearg.add_argument('--height', type=float, default=6, help='Display height')
parsearg.add_argument('--type', help='ew/ps/pr to select display', type=str, default="ew")
parsearg.add_argument('--bins', type=int, default=20, help='Histogram bins')
parsearg.add_argument('--xhist', type=str, help='Label for histogram X axis')
parsearg.add_argument('--yhist', type=str, help='Label for histogram Y axis')
parsearg.add_argument('--histlegend', type=str, nargs='*', help='Legends for histogram, successive strings')
parsearg.add_argument('--xaxt', action='store_true', help='Put X axis label on top')
parsearg.add_argument('--yaxr', action='store_true', help='Put Y axis label on right')
parsearg.add_argument('--histxrange', type=str, help='Range for Hist X axis')
parsearg.add_argument('--histyrange', type=str, help='Range for Hist Y axis')
parsearg.add_argument('--outfile', type=str, help='Output file')
parsearg.add_argument('--histcolour', type=str, default='b,g,r', help='Colour for histogram successive')

resargs = vars(parsearg.parse_args())
rfiles = resargs['integ']
title = resargs['title']
dims = (resargs['width'], resargs['height'])
typeplot = resargs['type']
bins = resargs['bins']
xtt = resargs['xaxt']
ytr = resargs['yaxr']
histxrange = rangearg.parserange(resargs['histxrange'])
histyrange = rangearg.parserange(resargs['histyrange'])
histcolour = string.split(resargs['histcolour'], ',')
outf = resargs['outfile']

if typeplot not in optdict:
    print "Unknown type", typeplot, "specified"
    sys.exit(2)
ycolumn, histxlab = optdict[typeplot]
if resargs['xhist'] is not None:
    histxlab = resargs['xhist']
    if histxlab == "none":
        histxlab = ""

histleg = resargs['histlegend']
if histleg is None:
    histleg = []

histylab = resargs['yhist']
if histylab is None:
    histylab = 'Occurrences (%)'

# Load up files of integration results

occlist = []
wtlist = []

for rf in rfiles:
    try:
        inp = np.loadtxt(rf, unpack=True)
    except IOError as e:
        print "Error loading EW file", rf
        print "Error was", e.args[1]
        sys.exit(102)

    if inp.shape[0] < 8:
        print "Expecting new format 8-column shape for", rf, "please convert"
        print "Shape was", inp.shape
        sys.exit(103)

    vals = inp[ycolumn]
    wt = np.ones_like(vals) * 100.0 / len(vals)
    occlist.append(vals)
    wtlist.append(wt)

# Step one is to do the histogram

fig = plt.figure(figsize=dims)
fig.canvas.set_window_title(title + ' Histogram')

if histyrange is not None:
    plt.ylim(*histyrange)
if histxrange is not None:
    plt.xlim(*histxrange)
    bins = np.linspace(*histxrange, num=bins)

ax = plt.gca()
ax.get_xaxis().get_major_formatter().set_useOffset(False)
while len(occlist) > len(histcolour):
    histcolour *= 2
histcolour = histcolour[0:len(occlist)]

plt.hist(occlist, bins=bins, color=histcolour, weights=wtlist)

if len(histleg) != 0:
    plt.legend(histleg)

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
    plt.xlabel(histxlab)
else:
    plt.xticks([])

# Save histogram output file if required

fig.tight_layout()
if outf is not None:
    plt.savefig(outf)
else:
    try:
        plt.show()
    except KeyboardInterrupt:
        pass

sys.exit(0)
