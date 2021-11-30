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
import trimarrays
import matplotlib.pyplot as plt
from astropy.modeling.tests.test_projections import pars
from bokeh.themes import default
from _pylief import parse
import remgeom
import miscutils
import strreplace
import re

filtfn = dict(BL='z', BR="r", UR="g", UL="i")
fmtch = re.compile('([FBIm]).*([UB][LR])')


def getfilt(hdr):
    """Get filter from FIRTS header"""
    global filtfn, fmtch
    try:
        return hdr['FILTER']
    except KeyError:
        pass
    try:
        fn = hdr['FILENAME']
        fm = fmtch.match(fn)
        if fm:
            ftp, quad = fm.groups()
            return  filtfn[quad]
    except KeyError:
        pass
    return  None

# Shut up warning messages


warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

rg = remgeom.load()

parsearg = argparse.ArgumentParser(description='Compare bias files and plot hist of differences', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', type=str, nargs=2, help='Pair of bias files')
parsearg.add_argument('--trim', type=str, help='rows:cols to trim to alternative to --ffre')
parsearg.add_argument('--ffref', type=str, help='Flat file for reference')
parsearg.add_argument('--replstd', type=float, default=5.0, help='Replace exceptional values > this with median')
parsearg.add_argument('--abs', action='store_true', help='Take absolute value of differfences')
parsearg.add_argument('--bins', type=int, default=10, help='Number of histogram bins')
parsearg.add_argument('--norm', type=str, help='Plot normal curse in specified colour')
parsearg.add_argument('--colourhist', type=str, default='b', help='Historgrapm colour')
parsearg.add_argument('--histalpha', type=float, default=0.75, help='Alpha value for historgram only if plotting norm curve')
parsearg.add_argument('--clip', type=int, default=5, help='Level at which we count exceiptionals')
parsearg.add_argument('--title', type=str, help='Title (otherwise generated from file dates)')

rg.disp_argparse(parsearg)

resargs = vars(parsearg.parse_args())
file1, file2 = resargs['files']
bins = resargs['bins']
absval = resargs['abs']
ffref = resargs['ffref']
rc = resargs['trim']
clip = resargs['clip']
replstd = resargs['replstd']
histalpha = resargs['histalpha']
colourhist = resargs['colourhist']
normplot = resargs['norm']
if normplot is None: histalpha = 1.0
title = resargs['title']

outfig = rg.disp_getargs(resargs)

if ffref is not None:
    ffreff = fits.open(ffref)
    ffrefim = trimarrays.trimzeros(trimarrays.trimnan(ffreff[0].data))
    ffreff.close()
    rows, cols = ffrefim.shape
elif rc is not None:
    try:
        rows, cols = map(lambda x: int(x), rc.split(':'))
    except ValueError:
        print("Unexpected --trim arg", rc, "expected rows:cols", file=sys.stderr)
        sys.exit(10)
else:
    print("No reference flat file or trim arg given", file=sys.stderr)
    sys.exit(11)

bf1 = fits.open(file1)
bim1 = bf1[0].data.astype(np.float32)
bh1 = bf1[0].header
try:
    bdate1 = Time(bh1['DATE-OBS']).datetime
except KeyError:
    bdate1 = datetime.datetime.now()
bf1.close()
f1 = getfilt(bh1)
if f1 is None:
    print("Cannot discover filter type from", file1, file=sys.stderr)
    sys.exit(12)

bf2 = fits.open(file2)
bim2 = bf2[0].data.astype(np.float32)
bh2 = bf2[0].header
try:
    bdate2 = Time(bh2['DATE-OBS']).datetime
except KeyError:
    bdate2 = datetime.datetime.now()
bf2.close()
f2 = getfilt(bh2)
if f2 is None:
    print("Cannot discover filter type from", file2, file=sys.stderr)
    sys.exit(12)

if f1 != f2:
    print("Different filter for", file1, "-", f1, "than", file2, "-", f2, file=sys.stderr)
    sys.exit(13)

bim1, bim2 = trimarrays.trimrc(rows, cols, bim1, bim2)

if replstd > 0.0:
    bim1 = strreplace.strreplace(bim1, replstd)
    bim2 = strreplace.strreplace(bim2, replstd)

bdiffs = (bim1 - bim2).flatten()
absdiffs = np.abs(bdiffs)
mv = np.round(absdiffs.mean())
mstd = absdiffs.std()
if absval:
    bdiffs = absdiffs
    bdiffs[bdiffs > clip * mstd] = mv
else:
    bdiffs[bdiffs < -clip * mstd] = -mv
    bdiffs[bdiffs > clip * mstd] = mv

plotfigure = rg.plt_figure()
plotfigure.canvas.manager.set_window_title("BIAS file differences")

plt.hist(bdiffs.flatten(), bins=bins, color=colourhist, alpha=histalpha)
medv = np.median(bdiffs)
stdv = bdiffs.std()
if normplot is not None:
    rv = norm(loc=medv, scale=stdv)
    xd = np.linspace(bdiffs.min(), bdiffs.max(), 200)
    yd = rv.pdf(xd) * float(bdiffs.size)
    plt.plot(xd, yd, color=normplot)
plt.xlabel("Differences in px values (med=%.3g std=%.3g)" % (medv, stdv))
if title is None:
    title = bdate1.strftime("Compare bias %Y-%m-%d %H:%M:%S -v- ") + bdate2.strftime("%Y-%m-%d %H:%M:%S")
title += "\nFor filter " + f1
plt.title(title)
if outfig is None:
    plt.show()
else:
    outfig = miscutils.replacesuffix(outfig, 'png')
    plotfigure.savefig(outfig)
    plt.close(outfig)
