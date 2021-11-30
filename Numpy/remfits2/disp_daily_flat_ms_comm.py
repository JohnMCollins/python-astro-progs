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
import miscutils
import parsetime
import datetime
import remget
import fitsops
import remfits

rg = remgeom.load()

parsearg = argparse.ArgumentParser(description='Plot std deviation versus mean of daily flats aligning to common area', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg, libdir=False, tempdir=False)
parsetime.parseargs_daterange(parsearg)
parsearg.add_argument('--limits', type=str, help='Lower:upper limit of means')
parsearg.add_argument('--cutlimit', type=str, default='all', choices=('all', 'limits', 'calclimits'), help='Point display and lreg calc, display all,')
parsearg.add_argument('--clipstd', type=float, help='Clip std devs this multiple different from std dev of std devs')
parsearg.add_argument('--xlabel', type=str, default='Mean value', help='X axis label')
parsearg.add_argument('--ylabel', type=str, default='Std deviation', help='Y axis label')
parsearg.add_argument('--pcolour', type=str, default='b', help='Plot points colour pre-reconfug')
parsearg.add_argument('--ncolour', type=str, default='g', help='Plot points colour post-reconfug')
parsearg.add_argument('--limscolour', type=str, default='k', help='Limit lines colour')
parsearg.add_argument('--limalpha', type=float, default=1, help='Limit line alpha')
parsearg.add_argument('--limls', type=str, default=':', help='Limit line style')
parsearg.add_argument('--regcolour', type=str, default='k', help='Regression colour')
parsearg.add_argument('--regls', type=str, default='-', help='Regression line style')
parsearg.add_argument('--regalpha', type=float, default=1, help='Regression alpha')
parsearg.add_argument('--trimedge', type=int, default=0, help='Amount to trim off edges of each image')
rg.disp_argparse(parsearg)

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
xlab = resargs['xlabel']
ylab = resargs['ylabel']
pcolour = resargs['pcolour']
ncolour = resargs['ncolour']
limscolour = resargs['limscolour']
limls = resargs['limls']
limalpha = resargs['limalpha']
regcolour = resargs['regcolour']
regls = resargs['regls']
regalpha = resargs['regalpha']
ofig = rg.disp_getargs(resargs)
clipstd = resargs['clipstd']
limits = resargs['limits']
cutlimit = resargs['cutlimit']
trimedge = resargs['trimedge']
lowerlim = upperlim = None

fieldselect = ["typ='flat'", "ind!=0", "gain=1", "rejreason IS NULL"]
try:
    dstring = parsetime.getargs_daterange(resargs, fieldselect)
except ValueError as e:
    print(e.args[0], file=sys.stderr)
    sys.exit(20)

if limits is not None:
    try:
        lowerlim, upperlim = [float(x) for x in limits.split(":")]
        if lowerlim >= upperlim:
            raise ValueError("Limits lower limit should be less than upper")
    except ValueError:
        limits = None

# Make ourselves a nice table of the common areas as startx, starty, endx, endy

Common_areas = dict()
dimsp = dict()
dimsn = dict()
for filter in 'griz':
    dimsp[filter] = d = remdefaults.get_geom(datetime.datetime(2018, 1, 1), filter)
    pstartx, pstarty, pcols, prows = d
    dimsn[filter] = d = remdefaults.get_geom(datetime.datetime(2020, 1, 1), filter)
    nstartx, nstarty, ncols, nrows = d
    pendx = pstartx + pcols
    pendy = pstarty + prows
    nendx = nstartx + ncols
    nendy = nstarty + nrows
    Common_areas[filter] = (max(pstartx, nstartx), max(pstarty, nstarty), min(pendx, nendx), min(pendy, nendy))

dbase, dbcurs = remdefaults.opendb()

dbcurs.execute("SELECT ind FROM iforbinf WHERE " + " AND ".join(fieldselect))

dbrows = dbcurs.fetchall()
if len(dbrows) < 20:
    print("Not enough data points found to plot", file=sys.stderr)
    sys.exit(2)

pmeans = dict(g=[], r=[], i=[], z=[])
pstdds = dict(g=[], r=[], i=[], z=[])
nmeans = dict(g=[], r=[], i=[], z=[])
nstdds = dict(g=[], r=[], i=[], z=[])

for fitsind, in dbrows:
    fbin = remget.get_saved_fits(dbcurs, fitsind)
    hdr, data = fitsops.mem_get(fbin)
    rf = remfits.RemFits()
    rf.init_from(hdr, data)
    csx, csy, cex, cey = Common_areas[rf.filter]
    data = rf.data[csx - rf.startx:cex - rf.startx, csy - rf.starty:cey - rf.starty]
    if trimedge != 0:
        data = data[trimedge:-trimedge, trimedge:-trimedge]
    m = data.mean()
    s = data.std()
    if rf.dimscr() == dimsp[rf.filter]:
        pmeans[rf.filter].append(m)
        pstdds[rf.filter].append(s)
    else:
        nmeans[rf.filter].append(m)
        nstdds[rf.filter].append(s)

lrpmeans = pmeans.copy()
lrpstdds = pstdds.copy()
lrnmeans = nmeans.copy()
lrnstdds = nstdds.copy()

if limits is not None and cutlimit != 'all':
    for filter in 'rgiz':
        mn = np.array(pmeans[filter])
        std = np.array(pstdds[filter])
        mvs = (mn >= lowerlim) & (mn <= upperlim)
        lrpmeans[filter] = mn[mvs]
        lrpstdds[filter] = std[mvs]
        mn = np.array(nmeans[filter])
        std = np.array(nstdds[filter])
        mvs = (mn >= lowerlim) & (mn <= upperlim)
        lrnmeans[filter] = mn[mvs]
        lrnstdds[filter] = std[mvs]
        if cutlimit == 'limits':
            pmeans[filter] = lrpmeans[filter]
            pstdds[filter] = lrpstdds[filter]
            nmeans[filter] = lrnmeans[filter]
            nstdds[filter] = lrnstdds[filter]

if clipstd is not None:
    for filter in 'rgiz':
        mn = np.array(pmeans[filter])
        std = np.array(pstdds[filter])
        sc = np.abs(std - std.mean()) < clipstd * std.std()
        pmeans[filter] = mn[sc]
        pstdds[filter] = std[sc]
        mn = np.array(lrpmeans[filter])
        std = np.array(lrpstdds[filter])
        sc = np.abs(std - std.mean()) < clipstd * std.std()
        lrpmeans[filter] = mn[sc]
        lrpstdds[filter] = std[sc]
        mn = np.array(nmeans[filter])
        std = np.array(nstdds[filter])
        sc = np.abs(std - std.mean()) < clipstd * std.std()
        nmeans[filter] = mn[sc]
        nstdds[filter] = std[sc]
        mn = np.array(lrnmeans[filter])
        std = np.array(lrnstdds[filter])
        sc = np.abs(std - std.mean()) < clipstd * std.std()
        lrnmeans[filter] = mn[sc]
        lrnstdds[filter] = std[sc]

minstd = min(min([np.min(x) for x in pstdds.values()]), min([np.min(x) for x in nstdds.values()]))
maxstd = max(max([np.max(x) for x in pstdds.values()]), max([np.max(x) for x in nstdds.values()]))

fig = rg.plt_figure()
fig.canvas.manager.set_window_title("std dev/mean of daily flats")

for filter, subp in ('i', 221), ('g', 222), ('z', 223), ('r', 224):

    plt.subplot(subp)
    plt.ylim(minstd, maxstd)
    plt.scatter(pmeans[filter], pstdds[filter], color=pcolour)
    plt.scatter(nmeans[filter], nstdds[filter], color=ncolour)
    plt.legend([filter + ' filter (pre-recon)', filter + " filter (post-recon)"], loc='upper left')
    if limits is not None and cutlimit != 'limits':
        plt.axvline(lowerlim, color=limscolour, ls=limls, alpha=limalpha)
        plt.axvline(upperlim, color=limscolour, ls=limls, alpha=limalpha)
    lrslope, lrintercept, lrr, lrp, lrstd = stats.linregress(lrpmeans[filter], lrpstdds[filter])
    lrx = np.array([min(lrpmeans[filter]), max(lrpmeans[filter])])
    lry = lrx * lrslope + lrintercept
    plt.plot(lrx, lry, color=regcolour, ls=regls, alpha=regalpha)
    lrslope, lrintercept, lrr, lrp, lrstd = stats.linregress(lrnmeans[filter], lrnstdds[filter])
    lrx = np.array([min(lrnmeans[filter]), max(lrnmeans[filter])])
    lry = lrx * lrslope + lrintercept
    plt.plot(lrx, lry, color=regcolour, ls=regls, alpha=regalpha)
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
