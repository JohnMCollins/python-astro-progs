#! /usr/bin/env python3

# @Author: John M Collins <jmc>
# @Date:   2018-08-23T14:20:00+01:00
# @Email:  jmc@toad.me.uk
# @Filename: dbobjdisp.py
# @Last modified by:   jmc
# @Last modified time: 2019-01-04T23:02:43+00:00

from astropy.io import fits
from astropy import wcs
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
from astropy.time import Time
import astroquery.utils as autils
import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import argparse
import sys
import datetime
import os.path
import objcoord
import trimarrays
import wcscoord
import warnings
import miscutils
import remdefaults
import remgeom
import remget
import remfits
import fitsops
import strreplace
import col_from_file
import find_results

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)
autils.suppress_vo_warnings()

rg = remgeom.load()

parsearg = argparse.ArgumentParser(description='Display mean and standard deviations of master flats', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg, tempdir=False, libdir=False)
parsearg.add_argument('--stderrmult', type=float, default=1.5, help='Multiple of std devs to allow for neat plot of errorbars')

figout = rg.disp_argparse(parsearg)

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
stderrmult = resargs['stderrmult']

figout = rg.disp_getargs(resargs)

db, dbcurs = remdefaults.opendb()

dbcurs.execute("SELECT month,year,filter,fitsind FROM forbinf WHERE year>2016 AND (year>2017 OR month>6) AND rejreason IS NULL AND gain=1 AND typ='flat' ORDER BY year,month")
forbrows = dbcurs.fetchall()

# Pairs of arrays to hold meams and standard deviations

filterres = dict(g=([], []), r=([], []), i=([], []), z=([], []))
datelist = []

lastmonth = lastyear = -1

for month, year, filter, fitsind in forbrows:

    if month != lastmonth or year != lastyear:  # NB we sorted it!
        dt = datetime.datetime(year=year, month=month, day=15, hour=12, minute=0, second=0)
        datelist.append(dt)
        lastmonth = month
        lastyear = year

    ffbin = remget.get_saved_fits(dbcurs, fitsind)
    hdr, data = fitsops.mem_get(ffbin)
    ff = remfits.RemFits()
    ff.init_from(hdr, data)
    p = filterres[filter]
    p[0].append(ff.meanval)
    p[1].append(ff.stdval)

plotfigure = rg.plt_figure()
plotfigure.canvas.set_window_title("Mean std/dev 4 filters")

maxv = -1
minv = 1e6
maxstd = -1

for filter in 'griz':
    maxv = max(maxv, max(filterres[filter][0]))
    minv = min(minv, min(filterres[filter][0]))
    maxstd = max(maxstd, max(filterres[filter][1]))

df = mdates.DateFormatter("%m/%Y")

for filter, subp in ('i', 221), ('g', 222), ('z', 223), ('r', 224):

    p = filterres[filter]
    means = p[0]
    stddevs = p[1]
    ax = plt.subplot(subp)
    if len(datelist) != len(means):
        print("Cannot print filter", filter, "datelist", len(datelist), "means", len(means), file=sys.stderr)
        continue
    plt.ylim(minv - stderrmult * maxstd, maxv + stderrmult * maxstd)
    plt.errorbar(datelist, means, stddevs)
    ax.xaxis.set_major_formatter(df)
    plt.legend([filter + " filter mean/std"])

plt.tight_layout()
if figout is None:
    plt.show()
else:
    figout = miscutils.replacesuffix(figout, ".png")
    plotfigure.savefig(figout)
    plt.close(plotfigure)
