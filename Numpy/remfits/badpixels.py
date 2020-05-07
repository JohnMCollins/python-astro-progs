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
import remgeom
import miscutils
import strreplace

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

rg = remgeom.load()

parsearg = argparse.ArgumentParser(description='Display images highlighting probable bad pixels', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', type=str, nargs='+', help='List of files to select grom')
parsearg.add_argument('--overbad', type=float, default=3.0, help='Upper limit of std devs beyond which regarded exceptional')
parsearg.add_argument('--underbad', type=float, default=3.0, help='Lower limit of std devs beyond which regarded exceptional')
parsearg.add_argument('--percentage', type=float, default=1.0, help='Multiple of expected occurences to consider pixel exceptional')
parsearg.add_argument('--zerotrim', action='store_true', help='Discount zeros from arrays first ')
parsearg.add_argument('--trimsides', type=int, default=0, help='Trim this number of rows and columns each side')
parsearg.add_argument('--clipzero', action='store_true', help='Clip zero rows/cols from display')
parsearg.add_argument('--colours', type=str, default='r:white,b,g', help='Comma separated colours for below,in range and above')
parsearg.add_argument('--wtitle', type=str, default='Invalid pixelss in image collection', help='Title for overall')
parsearg.add_argument('--title', type=str, default='Pixel map display', help='Label for pixel map')
parsearg.add_argument('--pietitle', type=str, default='Distribution of pixels', help='Lable for pie chart')
parsearg.add_argument('--xlab', type=str, default='Columns in images', help='X label for image displacy')
parsearg.add_argument('--ylab', type=str, default='Rows in images', help='Y label for image displacy')
rg.disp_argparse(parsearg, "dwin")
resargs = vars(parsearg.parse_args())

files = resargs['files']
overbad = resargs['overbad']
underbad = resargs['underbad']
percentage = resargs['percentage']
zerotrim = resargs['zerotrim']
trimsides = resargs['trimsides']
clipzero = resargs['clipzero']
wtitle = resargs['wtitle']
title = resargs['title']
pietitle = resargs['pietitle']
xlab = resargs['xlab']
ylab = resargs['ylab']
colours = resargs['colours'].split(',')

if len(colours) != 4:
    print("Expecting 4 colours", file=sys.stderr)
    sys.exit(20)
outfig = rg.disp_getargs(resargs)

resplus = np.zeros((1024, 1024))
resminus = np.zeros((1024, 1024))

filesdone = dict()
ndone = 0

minrows = mincols = 1000000

for file in files:

    if file in filesdone:
        continue

    filesdone[file] = 1

    try:
        ff = fits.open(file)
    except OSError as e:
        print("Cannot open", file, e.strerror, file=sys.stderr)
        continue

    fdat = ff[0].data
    ff.close()
    if np.count_nonzero(np.isnan(fdat)):
        fdat[np.isnan(fdat)] = 0.0

    trimmed = fdat
    if zerotrim:
        trimmed = trimarrays.trimzeros(fdat)

    minrows = min(minrows, trimmed.shape[0])
    mincols = min(mincols, trimmed.shape[1])
    if trimsides > 0:
        trimmed = trimmed[trimsides:-trimsides, trimsides:-trimsides]

    fdat = fdat.astype(np.float32)

    fmean = trimmed.mean()
    tstd = trimmed.std()

    if fmean == 0.0 or tstd == 0.0:
        print("Mean or std is zero file", file, file=sys.stderr)
        continue

    normed = (fdat - fmean) / tstd

    resplus += normed >= overbad
    resminus += normed <= -underbad
    ndone += 1

if ndone == 0:
    print("No files to process", file=sys.stderr)
    sys.exit(1)

ndone = float(ndone) / 100.0

if clipzero:
    resplus = resplus[0:minrows, 0:mincols]
    resminus = resminus[0:minrows, 0:mincols]

nr = norm(loc=0, scale=1)
uperc, lperc = nr.cdf([-overbad, -underbad]) * percentage
rejpos = resplus < uperc
rejneg = resminus < lperc
resplus[rejpos] = 0
resminus[rejneg] = 0
overlap = (resplus != 0) & (resminus != 0)
print("Plus", np.count_nonzero(resplus != 0), "Minus", np.count_nonzero(resminus != 0), "Overlap", np.count_nonzero(overlap))
resplus[overlap] = 0

result = resplus - resminus
result /= ndone

plotfigure = rg.plt_figure()
plotfigure.canvas.set_window_title(wtitle)
plt.subplot(121)
crange = [result.min(), result.max(), -lperc * 100, uperc * 100]
crange.sort()
cmap = colors.ListedColormap(colours[0:3])
norm = colors.BoundaryNorm(crange, 3, clip=True)
img = plt.imshow(result, cmap=cmap, norm=norm, origin='lower')
plt.colorbar(img, norm=norm, cmap=cmap, boundaries=crange, ticks=crange)
plt.xlabel(xlab)
plt.ylabel(ylab)
plt.title(title)
plt.subplot(122)
noverlap = np.count_nonzero(overlap)
nplus = np.count_nonzero(resplus)
nminus = np.count_nonzero(resminus)
print("Overall size", result.size, "Nplus", nplus, "Nminus", nminus - noverlap, "Overlap", noverlap)
if noverlap / float(result.size) < .01:
    plt.pie([nminus, result.size - nplus - nminus, nplus], colors=colours, labels=['Below', 'In range', 'Above'], autopct='%.2f', explode=[.2, 0, .2])
else:
    plt.pie([nminus - noverlap, result.size - nplus - nminus, nplus, noverlap], colors=colours, labels=['Below', 'In range', 'Above', 'Both'], autopct='%.2f', explode=[.2, 0, .2, .2])
plt.title(pietitle)
plt.tight_layout()
if outfig is None:
    plt.show()
else:
    outfig = miscutils.replacesuffix(outfig, 'png')
    plotfigure.savefig(outfig)
    plt.close(outfig)
