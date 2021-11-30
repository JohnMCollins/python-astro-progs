#! /usr/bin/env python3

import matplotlib.pyplot as plt
import matplotlib.patches as mp
import matplotlib.dates as mdates
import warnings
import astroquery.utils as autils
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)
autils.suppress_vo_warnings()
from scipy import stats
from matplotlib import colors
import numpy as np
import argparse
import sys
import math
import string
import remgeom
import dbops
import remdefaults
import dbremfitsobj
import os
import os.path
import subprocess
import trimarrays
import miscutils
import parsetime

# Shut up warning messages

rg = remgeom.load()

parsearg = argparse.ArgumentParser(description='Get plots of correlation of daily flat for cutoffs', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg)
parsetime.parseargs_daterange(parsearg)
parsearg.add_argument('--minimum', type=str, required=True, help='Minimum value to cut off or range as m:step:n')
parsearg.add_argument('--maximum', type=str, required=True, help='Maximum value to cut off or range as m:step:n')
parsearg.add_argument('--bymaxmin', action='store_true', help='Use maximum/minimum values rather than means')
parsearg.add_argument('--xlabel', type=str, help='X axis label')
parsearg.add_argument('--y1label', type=str, default='Correlation', help='Y1 axis label')
parsearg.add_argument('--y2label', type=str, default='Std deviation of fit', help='Y2 axis label')
parsearg.add_argument('--colour', type=str, default='b', help='Correlation colour')
parsearg.add_argument('--errorcolour', type=str, default='r', help='Error colour')
rg.disp_argparse(parsearg)

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
minimum = resargs['minimum']
maximum = resargs['maximum']
bymaxmin = resargs['bymaxmin']
xlab = resargs['xlabel']
y1lab = resargs['y1label']
y2lab = resargs['y2label']
colour = resargs['colour']
errorcolour = resargs['errorcolour']
ofig = rg.disp_getargs(resargs)

try:
    minbits = [float(p) for p in minimum.split(':')]
    maxbits = [float(p) for p in maximum.split(':')]
except ValueError as e:
    print("Could not decode min/max", minimum, "and", maximum, "error was", e.args[0], file=sys.stderr)
    sys.exit(10)

minval = maxval = None

if len(minbits) == 1:
    if len(maxbits) != 3:
        print("If minimum is single value maximum should be 3 values not", maximum, file=sys.stderr)
        sys.exit(11)
    minval = minbits[0]
    maxrange = np.arange(maxbits[0], maxbits[2] + maxbits[1], maxbits[1])
elif len(minbits) != 3:
    print("Expecting minimum to be one value or 3 not", minimum, file=sys.stderr)
    sys.exit(11)
elif len(maxbits) != 1:
    print("Expecting maximum to be 1 value when minimum is 3 not", maximum, file=sys.dtderr)
    sys.exit(11)
else:
    maxval = maxbits[0]
    minrange = np.arange(minbits[0], minbits[2] + minbits[1], minbits[1])

fieldselect = ["mean IS NOT NULL", "typ='flat'", "ind!=0", "gain=1"]

try:
    parsetime.getargs_daterange(resargs, fieldselect)
except ValueError as e:
    print(e.args[0], file=sys.stderr)
    sys.exit(20)

dbase, dbcurs = remdefaults.opendb()

fig = rg.plt_figure()
fig.canvas.manager.set_window_title("Exploration of cutoff point")

for filter, subp in ('i', 221), ('g', 222), ('z', 223), ('r', 224):

    dbcurs.execute("SELECT mean,std,minv,maxv FROM iforbinf WHERE " + " AND ".join(fieldselect + ["filter='" + filter + "'"]))
    rows = np.array(dbcurs.fetchall())

    if len(rows) < 20:
        print("Not enough data points found to plot", file=sys.stderr)
        sys.exit(2)

    means = np.array(rows[:, 0])
    stdds = np.array(rows[:, 1])
    minvs = np.array(rows[:, 2])
    maxvs = np.array(rows[:, 3])

    corrs = []
    errs = []

    if maxval is None:
        if bymaxmin:
            for m in maxrange:
                sc = (maxvs <= m) & (minvs >= minval)
                pmeans = means[sc]
                pstds = stdds[sc]
                lrslope, lrintercept, lrr, lrp, lrstd = stats.linregress(pmeans, pstds)
                corrs.append(lrr)
                errs.append(lrstd)
            if xlab is None:
                xlab = "cutoff maximum value min {:.0f}".format(minval)
        else:
            for m in maxrange:
                sc = (means <= m) & (means >= minval)
                pmeans = means[sc]
                pstds = stdds[sc]
                lrslope, lrintercept, lrr, lrp, lrstd = stats.linregress(pmeans, pstds)
                corrs.append(lrr)
                errs.append(lrstd)
            if xlab is None:
                xlab = "cutoff maximum mean value min {:.0f}".format(minval)
        xax = maxrange
    else:
        if bymaxmin:
            for m in minrange:
                sc = (minvs >= m) & (maxvs <= maxval)
                pmeans = means[sc]
                pstds = stdds[sc]
                lrslope, lrintercept, lrr, lrp, lrstd = stats.linregress(pmeans, pstds)
                corrs.append(lrr)
                errs.append(lrstd)
            if xlab is None:
                xlab = "cutoff minimum value max {:.0f}".format(maxval)
        else:
            for m in minrange:
                sc = (means >= m) & (means <= maxval)
                pmeans = means[sc]
                pstds = stdds[sc]
                lrslope, lrintercept, lrr, lrp, lrstd = stats.linregress(pmeans, pstds)
                corrs.append(lrr)
                errs.append(lrstd)
            if xlab is None:
                xlab = "cutoff minimum mean value max {:.0f}".format(maxval)
        xax = minrange

    ax = plt.subplot(subp)
    plt.plot(xax, corrs, color=colour)
    plt.legend([filter + " filter"], loc='upper center')
    plt.xlabel(xlab)
    plt.ylabel(y1lab)
    ax2 = ax.twinx()
    plt.plot(xax, errs, color=errorcolour)
    plt.ylabel(y2lab)

plt.tight_layout()
if ofig is None:
    plt.show()
else:
    ofig = miscutils.replacesuffix(ofig, 'png')
    fig.savefig(ofig)
