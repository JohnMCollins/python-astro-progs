#! /usr/bin/env python

import argparse
import matplotlib.pyplot as plt
import numpy as np
import os.path
import os
import sys
import string

parsearg = argparse.ArgumentParser(description='Display table of percent errors from fake spectra', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('pfile', type=str, nargs=1, help='Result file')
parsearg.add_argument('--title', help='Set window title', type=str, default="Percent error plot")
parsearg.add_argument('--outfig', type=str, help='Output figure')
parsearg.add_argument('--plotcolours', type=str, default='k,r,g,b,y,m,c', help='Colours for successive plots')
parsearg.add_argument('--ytrim', type=float, default=100.0, help='Trim percentages greater than this')
parsearg.add_argument('--ylim', type=float, default=0.0, help='Limit on Y display')
parsearg.add_argument('--xlab', type=str, help='Label for X axis', default='SNR level (dB)')
parsearg.add_argument('--ylab', type=str, help='Label for Y axis', default='Error %age')
parsearg.add_argument('--width', help="Width of plot", type=float, default=8)
parsearg.add_argument('--height', help="Height of plot", type=float, default=6)

resargs = vars(parsearg.parse_args())

spec = resargs['pfile'][0]
outfig = resargs['outfig']
plotcols = resargs['plotcolours']
xlab = resargs['xlab']
ylab = resargs['ylab']
ytrim = resargs['ytrim']
ylimit = resargs['ylim']

plt.rcParams['figure.figsize'] = (resargs['width'], resargs['height'])

fig = plt.gcf()
fig.canvas.set_window_title(resargs['title'])

try:
    inf = np.loadtxt(spec, unpack=True)
except IOError as e:
    print "Could not load percent file", spec, "error was", e.args[1]
    sys.exit(11)
except ValueError:
    print "Conversion error on", spec
    sys.exit(12)

plotcols = string.split(resargs['plotcolours'], ',') * (inf.shape[0] - 1)

snrvalues = inf[0]

for plotline in inf[1:]:
    colour = plotcols.pop(0)
    plotline[plotline > ytrim] = ytrim
    plt.plot(snrvalues, plotline, color=colour)

plt.xlabel(xlab)
plt.ylabel(ylab)
if ylimit > 0.0:
    plt.ylim(0.0, ylimit)
if outfig is None:
    try:
        plt.show()
    except KeyboardInterrupt:
        pass
else:
    plt.savefig(outfig)
sys.exit(0)
