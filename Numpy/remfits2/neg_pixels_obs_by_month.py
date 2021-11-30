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
import warnings
import miscutils
import remdefaults
import remgeom
import re
import remget
import fitsops
import remfits

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)
autils.suppress_vo_warnings()

rg = remgeom.load()

parsearg = argparse.ArgumentParser(description='Display negative pixels by month', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg, tempdir=False, libdir=False)
parsearg.add_argument('file', type=str, nargs=1, help='Negative pixel total file wuth filter in first col yyyy/mm in 2nd percent in last')
# parsearg.add_argument('--colours', type=str, default='k,g,b,r', help='Colours, comma sep for TL, TR, BL, RB')
rg.disp_argparse(parsearg)
resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
figout = rg.disp_getargs(resargs)
files = resargs['file']
# colours = resargs['colours'].split(',')
# if len(colours) != 4:
#     print("Expecting 4 colours in --colours", file=sys.stderr)
#     sys.exit(10)

dbase, dbcurs = remdefaults.opendb()

if figout is not None:
    figout = miscutils.removesuffix(figout, '.png')

plotfigure = rg.plt_figure()
plotfigure.canvas.manager.set_window_title("Negative pixel percentages")

pmtch = re.compile("([griz]):\s*(\d+)/(\d+).*&\s+([\d.]+)\s\\\\")

pcs = dict(g=[], r=[], i=[], z=[])
dts = dict(g=[], r=[], i=[], z=[])
try:
    with open(files[0]) as infile:
        for l in infile:
            mt = pmtch.match(l)
            if not mt:
                continue
            filter, year, month, pc = mt.groups()
            dt = datetime.datetime(int(year), int(month), 15, 12, 0, 0)
            dts[filter].append(dt)
            pcs[filter].append(float(pc))
except OSError as e:
    print(files[0], "gave error", e.args[1], file=sys.stderr)
    sys.exit(20)

dbcurs.execute("SELECT filter,fitsind,year,month FROM forbinf WHERE typ='bias' AND (year>2017 OR (year=2017 AND month>6)) ORDER BY year,month")
dbrows = dbcurs.fetchall()

msdts = dict(g=[], r=[], i=[], z=[])
means = dict(g=[], r=[], i=[], z=[])
stdds = dict(g=[], r=[], i=[], z=[])

for filter, fitsind, year, month in dbrows:
    fbin = remget.get_saved_fits(dbcurs, fitsind)
    hdr, data = fitsops.mem_get(fbin)
    rf = remfits.RemFits()
    rf.init_from(hdr, data)
    dt = datetime.datetime(year, month, 15, 12, 0, 0)
    msdts[filter].append(dt)
    means[filter].append(rf.meanval)
    stdds[filter].append(rf.stdval)

minpc = min([min(q) for q in pcs.values()])
maxpc = max([max(q) for q in pcs.values()])
maxstd = max([max(q) for q in stdds.values()])
minmean = min([min(q) for q in means.values()]) - maxstd
maxmean = max([max(q) for q in means.values()]) + maxstd

nc = 0
for filter, subp in ('i', 221), ('g', 222), ('z', 223), ('r', 224):

    ax = plt.subplot(subp)
    dtl = np.array(dts[filter])
    pcl = np.array(pcs[filter])
    sl = np.argsort(dtl)
    plt.plot(dtl[sl], pcl[sl], color='b')
    plt.ylim(minpc, maxpc)
    plt.ylabel("Percent")
    ax = ax.twinx()
    msdtl = np.array(msdts[filter])
    mns = np.array(means[filter])
    stds = np.array(stdds[filter])
    plt.errorbar(msdtl, mns, stds, color='k')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%y'))
    plt.ylim(minmean, maxmean)
    plt.ylabel("Mean bias")
    plt.legend([filter + ' filter'])
    nc += 1

plt.tight_layout()

if figout is not None:
    outfile = figout + ".png"
    plotfigure.savefig(outfile)
    plt.close(plotfigure)
else:
    try:
        plt.show()
    except KeyboardInterrupt:
        pass
