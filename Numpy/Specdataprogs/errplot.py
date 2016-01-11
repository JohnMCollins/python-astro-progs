#! /usr/bin/env python

import os
import sys
import math
import numpy as np
import matplotlib.pyplot as plt
import argparse
import string
import noise
import specinfo

parsearg = argparse.ArgumentParser(description='Display errors in spectral data', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('infofile', type=str, nargs=1, help='Info file')
parsearg.add_argument('--xlab', type=str, default='Datapoint number', help='Label for X axis')
parsearg.add_argument('--ylab', type=str, default='Signal to Noise (dB)', help='Label for Y axis')
parsearg.add_argument('--plotcolour', type=str, default='b', help='Colour for plot')
parsearg.add_argument('--median', type=str, help='Colour for median line if wanted')
parsearg.add_argument('--mean', type=str, help='Colour for mean line if wanted')
parsearg.add_argument('--outfile', type=str, help='Output file if required')
parsearg.add_argument('--width', type=float, help='Width of figure', default=8.0)
parsearg.add_argument('--height', type=float, help='Height of figure', default=6.0)

resargs = vars(parsearg.parse_args())

infofile = resargs['infofile'][0]
xlab = resargs['xlab']
ylab = resargs['ylab']
plotcol = resargs['plotcolour']
medianc = resargs['median']
meanc = resargs['mean']
outfile = resargs['outfile']
figs = (resargs['width'], resargs['height'])

if not os.path.isfile(infofile):
    infofile = miscutils.replacesuffix(infofile, specinfo.SUFFIX)

try:
    inf = specinfo.SpecInfo()
    inf.loadfile(infofile)
    ctrllist = inf.get_ctrlfile()
except specinfo.SpecInfoError as e:
    sys.stdout = sys.stderr
    print "Cannot load info file", infofile
    print "Error was:", e.args[0]
    sys.exit(100)

plt.rcParams['figure.figsize'] = figs

ctrllist.loadfiles()

errs = []

for dp in ctrllist.datalist:
    yv = dp.get_yvalues()
    ye = dp.get_yerrors()
    errs.append(noise.getnoise(yv, ye))

plt.plot(range(1, len(errs)+1), errs, color=plotcol)
if medianc is not None:
    plt.axhline(np.median(errs), color=medianc)
if meanc is not None:
    plt.axhline(np.mean(errs), color=meanc)
plt.xlabel(xlab)
plt.ylabel(ylab)
if outfile is None:
    plt.show()
else:
    plt.savefig(outf)
