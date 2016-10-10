#! /usr/bin/env python

import os
import sys
import math
import numpy as np
import matplotlib.pyplot as plt
import argparse
import string
import rangearg
import scipy.optimize as sopt

twopi = np.pi * 2.0

def sinefunc(x, dc, phase, amp):
    """Sine function for optimisation"""
    global period, twopi
    return  amp * np.sin(twopi * (phase + x/period)) + dc

parsearg = argparse.ArgumentParser(description='Phase fold plot', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('obsfile', type=str, nargs=1, help='Obs data file')
parsearg.add_argument('--outfile', type=str, help='Output file if required')
parsearg.add_argument('--width', type=float, help='Width of figure', default=8.0)
parsearg.add_argument('--height', type=float, help='Height of figure', default=6.0)
parsearg.add_argument('--tcol', type=int, default=0, help='Column with time in')
parsearg.add_argument('--icol', type=int, default=1, help='Column with intensity in')
parsearg.add_argument('--period', type=float, required=True, help='Period in question to fold')
parsearg.add_argument('--xlab', type=str, default='Time in days', help='Label for X axis')
parsearg.add_argument('--ylab', type=str, default='Intensity', help='Label for Y axis')
parsearg.add_argument('--xrange', type=str, help='X range')
parsearg.add_argument('--yrange', type=str, help='Y range')
parsearg.add_argument('--textfs', type=int, default=10, help='Plot text font size')
parsearg.add_argument('--scatter', action='store_false', help='Plot rather than scatter')
parsearg.add_argument('--phase', type=float, help='Plot sine curve with given phase')
parsearg.add_argument('--plotcolour', type=str, default='b', help='Colour of plot')
parsearg.add_argument('--phasecolour', type=str, help='Colour of sine curve if required')

resargs = vars(parsearg.parse_args())

obsfile = resargs['obsfile'][0]

plt.rcParams['figure.figsize'] = (resargs['width'], resargs['height'])

outf = resargs['outfile']
tcol = resargs['tcol']
icol = resargs['icol']
period = resargs['period']
xlab = resargs['xlab']
ylab = resargs['ylab']
textfs = resargs['textfs']
scatter = resargs['scatter']
plotc = resargs['plotcolour']
phasec = resargs['phasecolour']

yrange = rangearg.parserange(resargs['yrange'])
xrange = rangearg.parserange(resargs['xrange'])

try:
    f = np.loadtxt(obsfile, unpack=True)
    timings = f[tcol]
    intens = f[icol]
except IOError as e:
    print "Could not load obs  file", obsfile, "error was", e.args[1]
    sys.exit(11)
except ValueError:
    print "Conversion error on", obsfile
    sys.exit(12)
except IndexError:
    print "File of wrong shape -", obsfile

# Might as well start the timings from 0

timings -= timings.min()
timings %= period
s = timings.argsort()
stimings = timings[s]
sintens = intens[s]

if xrange is not None:
    plt.xlim(*xrange)
else:
    plt.xlim(0, period)
if yrange is not None:
    plt.ylim(*yrange)

if scatter:
    plt.scatter(stimings, sintens, color=plotc)
else:
    plt.plot(stimings, sintens, color=plotc)

if phasec is not None:
    popt, pcov = sopt.curve_fit(sinefunc, stimings, sintens, (sintens.mean(), 0.5, 1.0))
    perr = np.sqrt(np.diag(pcov))
    print "Dc =", popt[0], "phase =", popt[1], "amp =", popt[2], "err =", perr
    sc = sinefunc(stimings, *popt)
    plt.plot(stimings, sc, color=phasec)

plt.xlabel(xlab, fontsize=textfs)
plt.ylabel(ylab, fontsize=textfs)
if outf is not None:
    plt.savefig(outf)
else:
    plt.show()
