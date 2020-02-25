#! /usr/bin/env python3

# @Author: John M Collins <jmc>
# @Date:   2018-11-22T18:57:27+00:00
# @Email:  jmc@toad.me.uk
# @Filename: lcurve3.py
# @Last modified by:   jmc
# @Last modified time: 2019-01-04T23:10:14+00:00

from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
from astropy.io import fits
from astropy.time import Time
import datetime
import matplotlib.pyplot as plt
import matplotlib.patches as mp
from matplotlib import colors
import warnings
import numpy as np
import argparse
import sys
import math
import remgeom
import trimarrays
import re
import miscutils

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

filtfn = dict(BL='z', BR="r", UR="g", UL="i")
revfilt = dict()
for k, v in filtfn.items():
    revfilt[v] = k

qfilt = 'zrig'
fmtch = re.compile('([FB]).*([UB][LR])')

rg = remgeom.load()

parsearg = argparse.ArgumentParser(description='Observer effect of trim on mddian,mean', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', type=str, nargs='+', help='Files to analysee')
parsearg.add_argument('--forcetype', type=str, help='f or b to force daily flat/bias otherwise anything')
parsearg.add_argument('--title', type=str, default='Effect on trims on stats', help='Title for plot')
parsearg.add_argument('--colour', type=str, default='b', help='Colours for plot')
parsearg.add_argument('--outfig', type=str, help='Output file rather than display')
parsearg.add_argument('--start', type=int, default=0, help='Starting value of clip')
parsearg.add_argument('--step', type=int, default=5, help='Step value of clip')
parsearg.add_argument('--end', type=int, default=200, help='End value of clip"')
parsearg.add_argument('--side', type=str, default='all', help='Side to try trims all/left/right/top/bottom')
parsearg.add_argument('--others', type=int, default=100, help='Amount to trim others if only doing one side')
parsearg.add_argument('--xlabel', type=str, default='Rows/cols trimmed', help='X axis label')
parsearg.add_argument('--y1label', type=str, default='Mean values', help='Y1 axis label')
parsearg.add_argument('--y2label', type=str, default='Standard deviation', help='Y2 axis label')
parsearg.add_argument('--meancolour', type=str, default='b', help='Colour for plot of mean')
parsearg.add_argument('--stdcolour', type=str, default='g', help='Colour for plot of std dev')
rg.disp_argparse(parsearg)

resargs = vars(parsearg.parse_args())
files = resargs['files']
title = resargs['title']
ofig = resargs['outfig']
start = resargs['start']
step = resargs['step']
end = resargs['end']
colour = resargs['colour']
forcetype = resargs['forcetype']
side = resargs['side'][0]
others = resargs['others']
xlab = resargs['xlabel']
y1lab = resargs['y1label']
y2lab = resargs['y2label']
plotcol = resargs['meancolour']
stdcol = resargs['stdcolour']
rg.disp_getargs(resargs)

if forcetype is not None:
    if len(forcetype) == 0:
        forcetype = None
    else:
        forcetype = forcetype[0].upper()
        if forcetype != 'F' and forcetype != 'B':
            forcetype = None

nfigs = len(files)
fignum = 1
if ofig is not None:
    ofig = miscutils.removesuffix(ofig, '.png')

if side == 'a':
    xlab += "\nTrim from all sides"
else:
    if side == 'l':
        xlab += " from left side"
    elif side == 'r':
        xlab += " from right side"
    elif side == 't':
        xlab += ' from top'
    elif side == 'b':
        xlab += " from bottom"
    if others > 0:
        xlab += "\nwith %d from other sides" % others

for file in files:

    try:
        ff = fits.open(file)
    except (FileNotFoundError, PermissionError):
        print("Cannot open file", file, file=sys.stderr)
        continue

    fhdr = ff[0].header
    fdat = ff[0].data

    ff.close()

    try:
        dat = Time(fhdr['DATE-OBS'])
    except KeyError:
        print("Cannot find date in", file, file=sys.stderr)
        continue

    filter = None
    ftype = ""
    try:
        fname = fhdr['FILENAME']
        mtch = fmtch.match(fname)
        if mtch is not None:
            typ, seg = mtch.groups()
            if forcetype is not None and forcetype != typ:
                print("File is type", typ, "not", forcetype, "as required", file=sys.stderr)
                continue
            if typ == 'F':
                ftype = "Flat "
            elif typ == 'B':
                ftype = 'Bias '
            filter = filtfn[seg]
    except KeyError:
        if forcetype is not None:
            print("File is not of type", forcetype, "as required", file=sys.stderr)
            continue

    if filter is None:
        try:
            filter = fhdr['FILTER']
            ftype = "File "
        except KeyError:
            print("Cannot discover filter for filt", file, file=sys.stderr)
            continue

    ftitle = title + "\n" + ftype + "for filter " + filter + dat.datetime.strftime(" on %d/%m/%Y @ %H:%M:%S")

    curr = start

    # medians = []
    means = []
    stds = []
    trims = []

    fdat = trimarrays.trimzeros(trimarrays.trimnan(fdat))
    if side in 'lrtb' and others > 0:
        tl = tb = others
        tr = tt = -others
        if side == 'l':
            tl = 0
        elif side == 'r':
            tr = fdat.shape[1]
        elif side == 't':
            tt = fdat.shape[0]
        elif side == 'b':
            tb = 0
        fdat = fdat[tb:tt, tl:tr]

    if curr == 0:
        trims.append(curr)
        # medians.append(np.median(fdat))
        means.append(fdat.mean())
        stds.append(fdat.std())
        curr += step

    while curr <= end:
        if side == 'l':
            fdat = fdat[:, step:]
        elif side == 'r':
            fdat = fdat[:, :-step]
        elif side == 't':
            fdat = fdat[:-step]
        elif side == 'b':
            fdat = fdat[step:]
        else:
            fdat = fdat[step:-step, step:-step]
        trims.append(curr)
        # medians.append(np.median(fdat))
        means.append(fdat.mean())
        stds.append(fdat.std())
        curr += step

    plotfigure = rg.plt_figure()

    plt.title(ftitle)
    plt.xlabel(xlab)
    ax1 = plt.gca()
    plt.ylabel(y1lab)
    c1 = plt.plot(trims, means, color=plotcol)
    ax2 = ax1.twinx()
    c2 = plt.plot(trims, stds, color=stdcol)

    plt.legend(c1 + c2, ["Mean values", "Standard Deviation"], loc='best')

    plt.ylabel(y2lab)
    if ofig is not None:
        if nfigs > 1:
            outfile = ofig + "%.3d" % fignum + ".png"
            fignum += 1
        else:
            outfile = ofig + ".png"
        plotfigure.savefig(outfile)
        plt.close(plotfigure)

if ofig is None:
    plt.show()
