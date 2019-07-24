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
from matplotlib import colors
from astropy.modeling.tests.test_projections import pars
from bokeh.themes import default
from _pylief import parse
import remgeom
import miscutils
import strreplace

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

rg = remgeom.load()

parsearg = argparse.ArgumentParser(description='Show histogram of negative values after bias subtraction', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', type=str, nargs=2, help='image file and bias file')
parsearg.add_argument('--trim', type=str, help='rows:cols trim to')
parsearg.add_argument('--ffref', type=str, help='Flat file for reference')
parsearg.add_argument('--replstd', type=float, default=5.0, help='Replace exceptional values > this with median')
parsearg.add_argument('--delhigh', type=float, default=10.0, help='Delete values hight than this numbe of std devs from result')
parsearg.add_argument('--bins', type=int, default=30, help='Number of histogram bins')
parsearg.add_argument('--norm', type=str, help='Plot normal curse in specified colour')
parsearg.add_argument('--histalpha', type=float, default=0.75, help='Alpha value for historgram only if plotting norm curve')
parsearg.add_argument('--width', type=float, default=rg.width, help="Width of figure")
parsearg.add_argument('--height', type=float, default=rg.height, help="height of figure")
parsearg.add_argument('--outfig', type=str, help='Output figure if required')
parsearg.add_argument('--divff', action='store_true', help='Divide by flat field')

resargs = vars(parsearg.parse_args())
ffile, bfile = resargs['files']
ffref = resargs['ffref']
rc = resargs['trim']
replstd = resargs['replstd']
delhigh = resargs['delhigh']
width = resargs['width']
height = resargs['height']
outfig = resargs['outfig']
divff = resargs['divff']
bins = resargs['bins']
histalpha = resargs['histalpha']
normplot = resargs['norm']
if normplot is None: histalpha = 1.0

if ffref is not None:
    ffreff = fits.open(ffref)
    ffrefim = trimarrays.trimzeros(trimarrays.trimnan(ffreff[0].data))
    ffreff.close()
    rows, cols  = ffrefim.shape
elif rc is not None:
    try:
        rows, cols = map(lambda x: int(x), rc.split(':'))
    except ValueError:
        print("Unexpected --trim arg", rc, "expected rows:cols", file=sys.stderr)
        sys.exit(10)
    if divff:
        print("Sorry cannot specify --divff if just rows:cols given", file=sys.stderr)
        sys.exit(15)
else:
    print("No reference flat file or trim arg given", file=sys.stderr)
    sys.exit(11) 

ff = fits.open(ffile)
bf = fits.open(bfile)
fh = ff[0].header
bh = bf[0].header
fdat = Time(fh['DATE-OBS']).datetime
bdat = Time(bh['DATE-OBS']).datetime
fim = ff[0].data.astype(np.float32)
bim = bf[0].data.astype(np.float32)
ff.close()
bf.close()
fim, bim = trimarrays.trimrc(rows, cols, fim, bim)

if replstd > 0.0:
    bim = strreplace.strreplace(bim, replstd)

diffs = fim - bim
if divff:
	diffs /= ffrefim
diffs = diffs.flatten()
diffs = diffs[diffs <= np.median(diffs) + delhigh * diffs.std()]
medv = np.median(diffs)
stdv = diffs.std()
plotfigure = plt.figure(figsize=(width, height))
plotfigure.canvas.set_window_title("Distibution of sky level values")
plt.hist(diffs, bins=bins, alpha=histalpha)
if normplot is not None:
    rv = norm(loc=medv, scale=stdv)
    xd = np.linspace(diffs.min(), diffs.max(), 200)
    yd = rv.pdf(xd) * float(len(diffs))
    plt.plot(xd, yd, color=normplot)
    plt.axvline(medv, color=normplot)
tit = fdat.strftime("Comparison of sky from image dated %Y-%m-%d %H:%M:%S") + bdat.strftime(" and bias dated %Y-%m-%d %H:%M:%S")
plt.title(tit)
plt.xlabel("Sky pixels minus bias pixels (median %.2f std dev %.2f)" % (medv, stdv))
plt.ylabel("Number of occurrences")
if outfig is None:
    plt.show()
else:
    outfig = miscutils.replacesuffix(outfig, 'png')
    plotfigure.savefig(outfig)
    plt.close(outfig)

