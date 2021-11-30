#!  /usr/bin/env python3

# Get object data and maintain XML Database

from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
from astropy.io import fits
from astropy.time import Time
from scipy.stats import norm
import datetime
import numpy as np
import argparse
import warnings
import sys
import matplotlib.pyplot as plt
import remgeom
import miscutils
import strreplace
import parsetime
import remdefaults
import remget
import fitsops
import remfits
import mydateutil

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

rg = remgeom.load()
parsearg = argparse.ArgumentParser(description='Compare bias files and plot hist of differences', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsetime.parseargs_daterange(parsearg)
remdefaults.parseargs(parsearg, libdir=False, tempdir=False)
parsearg.add_argument('--replstd', type=float, default=5.0, help='Replace exceptional values > this with this value')
parsearg.add_argument('--abs', action='store_true', help='Take absolute value of differfences')
parsearg.add_argument('--bins', type=int, default=10, help='Number of histogram bins')
parsearg.add_argument('--norm', type=str, help='Plot normal curse in specified colour')
parsearg.add_argument('--colourhist', type=str, default='b', help='Historgrapm colour')
parsearg.add_argument('--histalpha', type=float, default=0.75, help='Alpha value for historgram only if plotting norm curve')
parsearg.add_argument("--limit", type=int, default=100, help='Limit on number to look at')

rg.disp_argparse(parsearg)
resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
replstd = resargs['replstd']
limit = resargs['limit']
bins = resargs['bins']
absval = resargs['abs']
histalpha = resargs['histalpha']
colourhist = resargs['colourhist']
normplot = resargs['norm']
if normplot is None: histalpha = 1.0

outfig = rg.disp_getargs(resargs)

fieldselect = []
parsetime.getargs_daterange(resargs, fieldselect)
if len(fieldselect) == 0:
    print("Need to select some dates, all is too many", file=sys.stderr)
    sys.exit(20)

fieldselect.append("ind!=0")
fieldselect.append("rejreason IS NULL")
fieldselect.append("gain=1")
fieldselect.append("typ='bias'")

dbase, curs = remdefaults.opendb()

curs.execute("SELECT ind FROM iforbinf WHERE " + " AND ".join(fieldselect))
indlist = curs.fetchall()
if len(indlist) > limit:
    print("Number of images of", len(indlist), "exceeds maximum of", limit, "give a different set of dates or --limit", file=sys.stderr)
    sys.exit(21)

dbyfilt = dict(g=[], i=[], r=[], z=[])
dshape = dict()

errors = 0

for ind, in indlist:

    ffmem = remget.get_saved_fits(curs, ind)
    hdr, data = fitsops.mem_get(ffmem)
    rf = remfits.RemFits(hdr, data)
    dbyfilt[rf.filter].append(rf.data)  # Use this as it's converted to float
    try:
        if dshape[rf.filter] != data.shape:
            print("Different shapes for ind", ind, data.shape, "previous", dshape[rf.filter], mydateutil.mysql_datetime(rf.date), file=sys.stderr)
            errors += 1
    except KeyError:
        dshape[rf.filter] = data.shape

if errors > 0:
    print("Aborting due to", errors, "errors", file=sys.stderr)
    sys.exit(22)

for filt in dbyfilt.keys():
    if len(dbyfilt[filt]) < 2:
        print("Insufficient bias files found for filter", filt, file=sys.stderr)
        errors += 1

if errors > 0:
    print("Aborting due to", errors, "errors", file=sys.stderr)
    sys.exit(23)

diffstab = dict()
for filt in 'griz':
    res = np.array([], dtype=np.float32)
    arr = dbyfilt[filt]
    while len(arr) > 1:
        nextd = arr.pop(0)
        for a in arr:
            diffs = a - nextd
            res = np.concatenate((res, diffs.flatten()))
    resmean = res.mean()
    resstdclip = res.std() * replstd
    res[res > resmean + resstdclip] = resmean + resstdclip
    res[res < resmean - resstdclip] = resmean - resstdclip
    diffstab[filt] = res

plotfigure = rg.plt_figure()
plotfigure.canvas.manager.set_window_title("BIAS file differences")

for filt, subp in ('i', 221), ('g', 222), ('z', 223), ('r', 224):

    diffs = diffstab[filt]
    ax = plt.subplot(subp)
    plt.hist(diffs, bins=bins, color=colourhist, alpha=histalpha)
    medv = np.median(diffs)
    stdv = diffs.std()
    if normplot is not None:
        rv = norm(loc=medv, scale=stdv)
        xd = np.linspace(diffs.min(), diffs.max(), 200)
        yd = rv.pdf(xd) * float(diffs.size)
        plt.plot(xd, yd, color=normplot)
    plt.xlabel("Differences between values")

plt.tight_layout()

if outfig is None:
    plt.show()
else:
    outfig = miscutils.replacesuffix(outfig, 'png')
    plotfigure.savefig(outfig)
    plt.close(outfig)
