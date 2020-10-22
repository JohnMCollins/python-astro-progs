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
import datetime

rg = remgeom.load()

parsearg = argparse.ArgumentParser(description='Plot linearity over time of daily flats with trims', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg, libdir=False, tempdir=False)
parsetime.parseargs_daterange(parsearg)
parsearg.add_argument('--limits', type=str, help='Lower:upper limit of means')
parsearg.add_argument('--trims', type=int, default=0, help='Amount to trim off each side')
parsearg.add_argument('--clipstd', type=float, help='Clip std devs this multiple different from std dev of std devs')
parsearg.add_argument('--filter', type=str, help='Restrict to given filter')
parsearg.add_argument('--title', type=str, default='Std deviation / mean over time', help='Title for plot')
parsearg.add_argument('--xlabel', type=str, default='Date', help='X axis label')
parsearg.add_argument('--ylabel', type=str, default='Std deviation/mean', help='Y axis label')
parsearg.add_argument('--colour', type=str, default='b', help='Plot points colour')
parsearg.add_argument('--marker', type=str, default=',', help='Marker style for scatter plot')
parsearg.add_argument('--dayint', type=int, help='Interval between dates')
rg.disp_argparse(parsearg)

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
title = resargs['title']
xlab = resargs['xlabel']
ylab = resargs['ylabel']
colour = resargs['colour']
marker = resargs['marker']
ofig = rg.disp_getargs(resargs)
filter = resargs['filter']
clipstd = resargs['clipstd']
trims = resargs['trims']
limits = resargs['limits']
dayint = resargs['dayint']

fieldselect = ["nrows IS NOT NULL", "typ='flat'", "ind!=0", "gain=1"]
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

dbase, dbcurs = remdefaults.opendb()

if filter is not None:
    fieldselect.append("filter=" + dbase.escape(filter))

dbcurs.execute("SELECT nrows,ncols,ind,date_obs FROM iforbinf WHERE " + " AND ".join(fieldselect))

dbrows = dbcurs.fetchall()
if len(dbrows) < 20:
    print("Not enough data points found to plot", file=sys.stderr)
    sys.exit(2)

means = []
stdds = []
fitsinds = []
dates = []
for rows, cols, fitsind, dobs in dbrows:
    try:
        ff = dbremfitsobj.getfits(dbcurs, fitsind)
        fdat = ff[0].data[0:rows, 0:cols].astype(np.float32)
        ff.close()
        if trims > 0:
            fdat = fdat[trims:-trims, trims:-trims]
        means.append(fdat.mean())
        stdds.append(fdat.std())
        fitsinds.append(fitsind)
        dates.append(dobs)
    except dbremfitsobj.RemObjError as e:
        print("Error fetching", fitsind, "error was", e.args[0])

means = np.array(means)
stdds = np.array(stdds)
fitsinds = np.array(fitsinds)
dates = np.array(dates)

rstdds = stdds / means

if clipstd is not None:
    sc = np.abs(stdds - stdds.mean()) / means < clipstd
    means = means[sc]
    stdds = stdds[sc]
    rstdds = rstdds[sc]
    fitsinds = fitsinds[sc]
    dates = dates[sc]

fig = rg.plt_figure()

mindate = dates.min()
maxdate = dates.max()
hrloc = mdates.HourLocator()
minloc = mdates.MinuteLocator()
secloc = mdates.SecondLocator()
df = mdates.DateFormatter("%Y-%m-%d")
ax = plt.gca()
ax.xaxis.set_major_locator(minloc)
ax.xaxis.set_major_formatter(df)

scatterp = plt.scatter(dates, rstdds, color=colour)

if dayint is None:
    dayint = 1
sd = mindate.toordinal()
ed = maxdate.toordinal() + 1
dlist = [datetime.datetime.fromordinal(x) for x in range(sd, ed, dayint)]
plt.xticks(dlist, rotation=45)

plt.title(title)
plt.xlabel(xlab)
plt.ylabel(ylab)
if ofig is None:
    plt.show()
else:
    ofig = miscutils.replacesuffix(ofig, 'png')
    plt.gcf().savefig(ofig)
