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

def strreplace(image, rs):
    """Replace things i> rs sttd evs from median with median"""
    med = np.median(image)
    s = rs * np.std(image)
    xc, yc = np.where(image - med > s)
    for x, y in zip(xc, yc):
        image[x,y] = med
    return image

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
parsearg.add_argument('--histalpha', type=float, default=0.75, help='Alpha value for historgram only if plotting norm curve')
parsearg.add_argument('--clip', type=int, default=5, help='Level at which we count exceiptionals')
parsearg.add_argument('--width', type=float, default=rg.width, help="Width of figure")
parsearg.add_argument('--height', type=float, default=rg.height, help="height of figure")
parsearg.add_argument('--outfig', type=str, help='Output figure if required')

resargs = vars(parsearg.parse_args())
file1, file2 = resargs['files']
bins = resargs['bins']
absval = resargs['abs']
ffref = resargs['ffref']
rc = resargs['trim']
clip = resargs['clip']
replstd = resargs['replstd']
histalpha = resargs['histalpha']
normplot = resargs['norm']
if normplot is None: histalpha = 1.0
width = resargs['width']
height = resargs['height']
outfig = resargs['outfig']

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
else:
    print("No reference flat file or trim arg given", file=sys.stederr)
    sys.exit(11) 

bf1 = fits.open(file1)
bim1 = bf1[0].data.astype(np.float32)
bdate1 = Time(bf1[0].header['DATE']).datetime
bf1.close()

bf2 = fits.open(file2)
bim2 = bf2[0].data.astype(np.float32)
bdate2 = Time(bf2[0].header['DATE']).datetime
bf2.close()

bim1, bim2 = trimarrays.trimrc(rows, cols, bim1, bim2)

if replstd > 0.0:
    bim1 = strreplace(bim1, replstd)
    bim2 = strreplace(bim2, replstd)
    
bdiffs = (bim1 - bim2).flatten()
absdiffs = np.abs(bdiffs)
mv = np.round(absdiffs.mean())
mstd = absdiffs.std()
if absval:
    bdiffs = absdiffs
    bdiffs[bdiffs > clip * mstd] = mv
else:
    bdiffs[bdiffs < -clip * mstd] = - mv
    bdiffs[bdiffs > clip * mstd] = mv

plotfigure = plt.figure(figsize=(width, height))
plotfigure.canvas.set_window_title("BIAS file differences")

plt.hist(bdiffs.flatten(), bins=bins, alpha=histalpha)
medv = np.median(bdiffs)
stdv = bdiffs.std()
if normplot is not None:
    rv = norm(loc=medv, scale=stdv)
    xd = np.linspace(bdiffs.min(), bdiffs.max(), 200)
    yd = rv.pdf(xd) * float(len(bdiffs.flatten()))
    plt.plot(xd, yd, color=normplot)
plt.xlabel("Differences in px values (med=%.3g std=%.3g" % (medv, stdv))
plt.title("Compare bias" + bdate1.strftime(" %Y-%m-%d %H:%M:%S -v- ") + bdate2.strftime("%Y-%m-%d %H:%M:%S"))
if outfig is None:
    plt.show()
else:
    outfig = miscutils.replacesuffix(outfig, 'png')
    plotfigure.savefig(outfig)
    plt.close(outfigure)
