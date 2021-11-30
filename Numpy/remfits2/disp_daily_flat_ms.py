#! /usr/bin/env python3

# @Author: John M Collins <jmc>
# @Date:   2018-11-22T18:57:27+00:00
# @Email:  jmc@toad.me.uk
# @Filename: lcurve3.py
# @Last modified by:   jmc
# @Last modified time: 2019-01-04T23:10:14+00:00

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

rg = remgeom.load()

parsearg = argparse.ArgumentParser(description='Plot std deviation versus mean of daily flats', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg, libdir=False, tempdir=False)
parsetime.parseargs_daterange(parsearg)
parsearg.add_argument('--limits', type=str, help='Lower:upper limit of means')
parsearg.add_argument('--cutlimit', type=str, default='all', choices=('all', 'limits', 'calclimits'), help='Point display and lreg calc, display all,')
parsearg.add_argument('--clipstd', type=float, help='Clip std devs this multiple different from std dev of std devs')
parsearg.add_argument('--xlabel', type=str, default='Mean value', help='X axis label')
parsearg.add_argument('--ylabel', type=str, default='Std deviation', help='Y axis label')
parsearg.add_argument('--colour', type=str, default='b', help='Plot points colour')
parsearg.add_argument('--limscolour', type=str, default='k', help='Limit lines colour')
parsearg.add_argument('--regcolour', type=str, default='k', help='Regression colour')
rg.disp_argparse(parsearg)

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
xlab = resargs['xlabel']
ylab = resargs['ylabel']
colour = resargs['colour']
limscolour = resargs['limscolour']
regcolour = resargs['regcolour']
ofig = rg.disp_getargs(resargs)
clipstd = resargs['clipstd']
limits = resargs['limits']
cutlimit = resargs['cutlimit']
lowerlim = upperlim = None

fieldselect = ["mean IS NOT NULL", "typ='flat'", "ind!=0", "gain=1", "rejreason IS NULL"]
try:
    dstring = parsetime.getargs_daterange(resargs, fieldselect)
except ValueError as e:
    print(e.args[0], file=sys.stderr)
    sys.exit(20)

if ofig is None:
    outputfile = None

if limits is not None:
    try:
        lowerlim, upperlim = [float(x) for x in limits.split(":")]
        if lowerlim >= upperlim:
            raise ValueError("Limits lower limit should be less than upper")
    except ValueError:
        limits = None

dbase, dbcurs = remdefaults.opendb()

dbcurs.execute("SELECT mean,std,ind,filter FROM iforbinf WHERE " + " AND ".join(fieldselect))

dbrows = dbcurs.fetchall()
if len(dbrows) < 20:
    print("Not enough data points found to plot", file=sys.stderr)
    sys.exit(2)

means = dict(g=[], r=[], i=[], z=[])
stdds = dict(g=[], r=[], i=[], z=[])

for mn, std, ind, filter in dbrows:
    means[filter].append(mn)
    stdds[filter].append(std)

lrmeans = means.copy()
lrstdds = stdds.copy()
if limits is not None and cutlimit != 'all':
    for filter in 'rgiz':
        mn = np.array(means[filter])
        std = np.array(stdds[filter])
        mvs = (mn >= lowerlim) & (std <= upperlim)
        lrmeans[filter] = means[mvs]
        lrstdds[filter] = stdds[mvs]
        if cutlimit == 'limits':
            means[filter] = lrmeans[filter]
            stdds[filter] = lrstdds[filter]

if clipstd is not None:
    for filter in 'rgiz':
        mn = np.array(means[filter])
        std = np.array(stdds[filter])
        sc = np.abs(std - std.mean()) < clipstd * std.std()
        means[filter] = mn[sc]
        stdds[filter] = std[sc]
        mn = np.array(lrmeans[filter])
        std = np.array(lrstdds[filter])
        sc = np.abs(std - std.mean()) < clipstd * std.std()
        lrmeans[filter] = mn[sc]
        lrstdds[filter] = std[sc]

minstd = min([np.min(x) for x in stdds.values()])
maxstd = max([np.max(x) for x in stdds.values()])

fig = rg.plt_figure()
fig.canvas.manager.set_window_title("std dev/mean of daily flats")

for filter, subp in ('i', 221), ('g', 222), ('z', 223), ('r', 224):

    plt.subplot(subp)
    plt.ylim(minstd, maxstd)
    scatterp = plt.scatter(means[filter], stdds[filter], color=colour)
    plt.legend([filter + ' filter'], loc='upper left')
    if limits is not None and cutlimit != 'limits':
        plt.axvline(lowerlim, color=limscolour)
        plt.axvline(upperlim, color=limscolour)
    lrslope, lrintercept, lrr, lrp, lrstd = stats.linregress(lrmeans[filter], lrstdds[filter])
    lrx = np.array([min(lrmeans[filter]), max(lrmeans[filter])])
    lry = lrx * lrslope + lrintercept
    plt.plot(lrx, lry, color=regcolour)
    plt.xlabel(xlab)
    plt.ylabel(ylab)

plt.tight_layout()
if ofig is None:
    try:
        plt.show()
    except KeyboardInterrupt:
        pass
else:
    ofig = miscutils.replacesuffix(ofig, ".png")
    fig.savefig(ofig)
    plt.close(fig)
