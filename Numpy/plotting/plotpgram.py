#! /usr/bin/env python

import argparse
import matplotlib.pyplot as plt
import numpy as np
import os.path
import os
import sys
import string
import rangearg

parsearg = argparse.ArgumentParser(description='Display bar chart of periods')
parsearg.add_argument('--outfig', type=str, help='Output figure')
parsearg.add_argument('--resdir', type=str, help='Directory if not same as spectrum data')
parsearg.add_argument('--barwidth', type=float, default=.01, help='Bar width')
parsearg.add_argument('--colour', type=str, default='blue', help='Line/bar colour')
parsearg.add_argument('--maxfile', type=str, help='File for maxima values')
parsearg.add_argument('--maxnum', type=int, default=5, help='Number of highest maxima to take')
parsearg.add_argument('--maxcol', type=str, default='green', help='Colour of lines denoting maxima') 
parsearg.add_argument('spec', type=str, help='Spectrum file')
parsearg.add_argument('--xlab', type=str, help='Label for X axis', default='Period in days')
parsearg.add_argument('--ylab', type=str, help='Label for Y axis', default='Probability that period is correct')
parsearg.add_argument('--yaxr', action='store_true', help='Put Y axis label on right')
parsearg.add_argument('--yrange', type=str, help='Range for Y axis')
parsearg.add_argument('--xaxt', action='store_true', help='Put X axis label on top')
parsearg.add_argument('--xrange', type=str, help='Range for X axis')
parsearg.add_argument('--fork', action='store_true', help='Fork off daemon process to show plot and exit')
parsearg.add_argument('--title', help='Set window title', type=str, default="Periodogram display")
parsearg.add_argument('--legend', type=str, help='Specify legend')
parsearg.add_argument('--width', help="Width of plot", type=float, default=4)
parsearg.add_argument('--height', help="Height of plot", type=float, default=3)

resargs = vars(parsearg.parse_args())

spec = resargs['spec']
outfig = resargs['outfig']
resdir = resargs['resdir']
width = resargs['barwidth']
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
if resdir is None:
    resdir = os.path.dirname(spec)
if len(resdir) == 0:
    resdir = os.getcwd()
elif not os.path.isdir(resdir):
    print "No results directory", resdir
    errors += 1
if width <= 0:
    print "Cannot have -ve or zero width"
    errors += 1

plt.rcParams['figure.figsize'] = (resargs['width'], resargs['height'])

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

if xrange is not None:
    plt.xlim(*xrange)
if yrange is not None:
    plt.ylim(*yrange)
plt.plot(periods, amps, color=col)
if len(ylab) == 0:
    plt.yticks([])
else:
    if ytr:
        plt.gca().yaxis.tick_right()
        plt.gca().yaxis.set_label_position("right")
    plt.ylabel(ylab)
if len(xlab) == 0:
    plt.xticks([])
else:
    if xtt:
        plt.gca().xaxis.tick_top()
        plt.gca().xaxis.set_label_position('top')
    plt.xlabel(xlab)
if exlegend is not None:
    plt.legend([exlegend], handlelength=0)

maxfile = resargs['maxfile']
if maxfile is not None:
	try:
		maxx, maxy = np.loadtxt(maxfile, unpack=True)
		maxnum = resargs['maxnum']
		if len(maxx) < maxnum: maxnum = len(maxx)
		if maxnum > 0:
			sortl = np.argsort(maxy)[-maxnum:]
			maxx = maxx[sortl]
			maxy = maxy[sortl]
			mcol = resargs['maxcol']
			for m in maxx:
				plt.axvline(m, color=mcol)
	except IOError as e:
		print "Could not load maxima file", maxfile, "error was", e.args[1]
	except ValueError:
		print "Conversion error on", maxfile

if outfig is not None:
    plt.savefig(outfig)
    sys.exit(0)
if not forkoff or os.fork() == 0:
    try:
        plt.show()
    except KeyboardInterrupt:
        pass

