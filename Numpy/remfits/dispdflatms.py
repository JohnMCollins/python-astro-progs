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
import trimarrays

# Shut up warning messages

rg = remgeom.load()
mydbname = remdefaults.default_database()
tmpdir = remdefaults.get_tmpdir()

parsearg = argparse.ArgumentParser(description='Plot std deviation versus mean of daily flatsl', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('--database', type=str, default=mydbname, help='Database to use')
parsearg.add_argument('--tempdir', type=str, default=tmpdir, help='Temp directory to unload files')
parsearg.add_argument('--divmean', action='store_true', help="Divide std dev by mean")
parsearg.add_argument('--limits', type=str, help='Lower:upper limit of means')
parsearg.add_argument('--cutlimit', action='store_true', help='Cut plot a limits')
parsearg.add_argument('--clipstd', type=float, help='Clip std devs this multiple different from std dev of std devs')
parsearg.add_argument('--filter', type=str, help='Restrict to given filter')
parsearg.add_argument('--title', type=str, default='Mean count of daily flats v Std devl', help='Title for plot')
parsearg.add_argument('--xlabel', type=str, default='Mean value', help='X axis label')
parsearg.add_argument('--ylabel', type=str, default='Std deviation', help='Y axis label')
parsearg.add_argument('--outfig', type=str, help='Output file rather than display')
parsearg.add_argument('--colour', type=str, default='b', help='Plot points colour')
parsearg.add_argument('--limscolour', type=str, default='k', help='Limit lines colour')
parsearg.add_argument('--regcolour', type=str, default='k', help='Regression colour')
parsearg.add_argument('--width', type=float, default=rg.width, help="Width of figure")
parsearg.add_argument('--height', type=float, default=rg.height, help="height of figure")
parsearg.add_argument('--labsize', type=int, default=10, help='Label and title font size')
parsearg.add_argument('--ticksize', type=int, default=10, help='Tick font size')

resargs = vars(parsearg.parse_args())
mydbname = resargs['database']
title = resargs['title']
xlab = resargs['xlabel']
ylab = resargs['ylabel']
ofig = resargs['outfig']
colour = resargs['colour']
limscolour = resargs['limscolour']
regcolour = resargs['regcolour']
width = resargs['width']
height = resargs['height']
labsize = resargs['labsize']
ticksize = resargs['ticksize']
filter = resargs['filter']
divmean = resargs['divmean']
clipstd = resargs['clipstd']
limits = resargs['limits']
cutlimit = resargs['cutlimit']
lowerlim = upperlim = None
if limits is not None:
    try:
        lowerlim, upperlim = [float(x) for x in limits.split(":")]
        if lowerlim >= upperlim:
            raise ValueError("Limits lower limit should be less than upper")
    except ValueError:
        limits = None

if ofig is not None:
    ofig = os.path.abspath(ofig)

try:
    os.chdir(tmpdir)
except FileNotFoundError:
    print("Unable to select temporary directory", tmpdir, file=sys.stderr)
    sys.exit(100)

dbase = dbops.opendb(mydbname)
dbcurs = dbase.cursor()

plt.rc('xtick', labelsize=ticksize)
plt.rc('ytick', labelsize=ticksize)

if filter is None:
    dbcurs.execute("SELECT mean,std FROM iforbinf WHERE mean IS NOT NULL AND typ='flat' AND ind!=0 AND gain=1")
else:
    dbcurs.execute("SELECT mean,std FROM iforbinf WHERE mean IS NOT NULL AND typ='flat' AND ind!=0 AND gain=1 AND filter=" + dbase.escape(filter))

rows = np.array(dbcurs.fetchall())
if len(rows) < 20:
    print("Not enough data points found to plot", file=sys.stderr)
    sys.exit(2)

means = np.array(rows[:, 0])
stdds = np.array(rows[:, 1])
if limits is not None and cutlimit:
    mvs = (means >= lowerlim) & (means <= upperlim)
    means = means[mvs]
    stdds = stdds[mvs]
if divmean:
    stdds /= means
    stdds *= 100.0

if clipstd is not None:
    sc = np.abs(stdds - stdds.mean()) < clipstd * stdds.std()
    means = means[sc]
    stdds = stdds[sc]
ass = np.argsort(stdds)
means = means[ass]
stdds = stdds[ass]
ass = np.argsort(means)
means = means[ass]
stdds = stdds[ass]

plt.figure(figsize=(width, height))
plt.scatter(means, stdds, color=colour)
plt.xlabel(xlab, fontsize=labsize)
plt.ylabel(ylab, fontsize=labsize)
if limits is not None and not cutlimit:
    plt.axvline(lowerlim, color=limscolour)
    plt.axvline(upperlim, color=limscolour)
lrslope, lrintercept, lrr, lrp, lrstd = stats.linregress(means, stdds)
lrx = np.array([means.min(), means.max()])
lry = lrx * lrslope + lrintercept
plt.plot(lrx, lry, color=regcolour)
plt.title(title + "\n" + "Slope %.6g Intercept %.6g Correlation %.6g" % (lrslope, lrintercept, lrr), fontsize=labsize)
if ofig is None:
    plt.show()
else:
    plt.gcf().savefig(ofig)
