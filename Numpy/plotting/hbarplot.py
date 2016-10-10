#! /usr/bin/env python

# Integrate the H alpha peaks to get figures for the total values,
# assume continuum is normalised at 1 unless otherwise specified

import argparse
import os.path
import sys
import string
import numpy as np
import matplotlib.pyplot as plt

def add_vals(patchlist, percents):
    """Put in percentage display if possible"""
    global fontsz, txtlim
    for ptch, pc in zip(patchlist, percents):
        if pc < txtlim: continue
        px, py = ptch.get_xy()
        wid = ptch.get_width()
        ht = ptch.get_height()
        plt.text(0.5*wid + px, 0.5*ht + py, "%.0f%%" % pc, ha='center', va='center', fontsize=fontsz)

# According to type of display select column, xlabel  for hist, ylabel for plot

parsearg = argparse.ArgumentParser(description='Horizontal bar percentage plot', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('ranges', type=str, nargs='+', help='pairs of values for EW PR Skew Kurt 82.6 and 41.3')
parsearg.add_argument('--outfile', type=str, help='Output file if required, else display')
parsearg.add_argument('--width', type=float, default=8, help='Display width')
parsearg.add_argument('--height', type=float, default=6, help='Display height')
parsearg.add_argument('--mcolour', type=str, default='b', help='Colour for 82.6 part')
parsearg.add_argument('--hcolour', type=str, default='y', help='Colour for 41.3 part')
parsearg.add_argument('--alpha', type=float, default=0.75, help='Alpha for bars')
parsearg.add_argument('--barheight', type=float, default=0.5, help='Bar height')
parsearg.add_argument('--xlim', type=float, default=-1, help='Limit of x value default=largest')
parsearg.add_argument('--xlab', type=str, default='Percent', help='Label for x axis')
parsearg.add_argument('--ylab', type=str, default='Measurement', help='Label for y axis')
parsearg.add_argument('--textfs', type=int, default=10, help='Font size for labels')
parsearg.add_argument('--title', type=str, help='Title for plot')
parsearg.add_argument('--net', action='store_true', help='Take net value from second figure')
parsearg.add_argument('--txtlim', type=float, default=1.0, help='Percentage below which we do not display')
parsearg.add_argument('--wcase', type=float, default=-1.0, help='Mark in worst case')
parsearg.add_argument('--wctext', type=str, default='Worst case', help='Label for worst case line')
parsearg.add_argument('--wcasey', type=float, default=0.0, help='Y pos for worst case')
parsearg.add_argument('--wcylim', type=float, default=1.0, help='Limit of wc line')
parsearg.add_argument('--wcasex', type=float, default=0.5, help='X offset for worst case')
parsearg.add_argument('--legloc', type=str, default='best', help='Legend loc')

resargs = vars(parsearg.parse_args())
plt.rcParams['figure.figsize'] = (resargs['width'], resargs['height'])

rangeargs = resargs['ranges']
outfile = resargs['outfile']
mcolour = resargs['mcolour']
hcolour = resargs['hcolour']
alpha = resargs['alpha']
barheight = resargs['barheight']
xlim = resargs['xlim']
xlab = resargs['xlab']
ylab = resargs['ylab']
fontsz = resargs['textfs']
title = resargs['title']
net = resargs['net']
txtlim = resargs['txtlim']
wcase = resargs['wcase']
legloc= resargs['legloc']
wctext = resargs['wctext']
wcasey = resargs['wcasey']
wcasex = resargs['wcasex']
wcylim = resargs['wcylim']

if len(rangeargs) != 8:
    print "Expecting 8 numbers as args"
    sys.exit(10)

try:
    em, ee, pm, pe, sm, se, km, ke = [float(x) for x in rangeargs]
except TypeError:
    print "Wrong numeric argument as args"
    sys.exit(11)

labels = ['EW', 'PR', 'Skewness', 'Kurtosis']
mvals = [em, pm, sm, km]
evals = [ee, pe, se, ke]

rlabels = [x for x in reversed(labels)]
rmvals = np.array([x for x in reversed(mvals)])
revals = np.array([x for x in reversed(evals)])
if net: revals -= rmvals

ypos = np.arange(4)
patches = plt.barh(ypos, rmvals, align='center', alpha=alpha, color=mcolour, height=barheight)
add_vals(patches, rmvals)
leftsides = [p.get_width() for p in patches]
epatches = plt.barh(ypos, revals, align='center', alpha=alpha, color=hcolour, left=leftsides, height=barheight)
add_vals(epatches, revals)
plt.yticks(ypos, rlabels, fontsize=fontsz)
plt.xlabel(xlab, fontsize=fontsz)
plt.ylabel(ylab, fontsize=fontsz)
if title is not None:
    plt.title(title, fontsize=fontsz)
if wcase > 0.0:
    plt.axvline(wcase, color='k', label='_nolegend_', ymax=wcylim)
    plt.text(wcase+wcasex, wcasey, wctext, rotation=90, fontsize=fontsz)
if xlim > 0.0:
    plt.xlim(0, xlim)
plt.legend(['82.6 days', '41.3 days'], loc=legloc)

if outfile is None:
    try:
        plt.show()
    except KeyboardInterrupt:
        pass
else:
    plt.savefig(outfile)
sys.exit(0)
