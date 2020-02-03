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
import scipy.stats as ss
import matplotlib.pyplot as plt
import matplotlib.patches as mp
from matplotlib import colors
import argparse
import sys
import datetime
import os.path
import trimarrays
import warnings
import miscutils
import strreplace
import remgeom

rg = remgeom.load()

parsearg = argparse.ArgumentParser(description='Display image files raw', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', type=str, nargs='+', help='File names to display')
parsearg.add_argument('--title', type=str, default="Image display", help="Title for each plot")
parsearg.add_argument('--xlabel', type=str, default="Column number", help="X xxis label")
parsearg.add_argument('--ylabel', type=str, default="Row number", help="Y xxis label")
parsearg.add_argument('--figout', type=str, help='File to output figure(s) to')
parsearg.add_argument('--percentiles', type=float, nargs='+', required=True, help="Percentiles to split at")
parsearg.add_argument('--histbins', type=int, default=20, help='Bins for histogram')
parsearg.add_argument('--colourhist', type=str, default='b', help='Colour of historgram')
parsearg.add_argument('--histtitle', type=str, default='Distribution normalised to mean', help='Histogram Title')
parsearg.add_argument('--histxlab', type=str, default='Pixel value normalised to mean', help='Label for histogram X axis')
parsearg.add_argument('--histylab', type=str, default='Occurences of vaalue', help='Label for histogram Y axis')
parsearg.add_argument('--addsk', action='store_false', help='Add stats to histogram title')
rg.disp_argparse(parsearg, "dwin")

resargs = vars(parsearg.parse_args())

# The reason why we don't get RA and DECL info out of this is because we have
# to adjust for proper motion which requires Python 3 (as the versions of astropy that
# support it only run with that)

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)
autils.suppress_vo_warnings()

files = resargs['files']
figout = resargs['figout']
percentiles = resargs['percentiles']
title = resargs['title']
xlab = resargs['xlabel']
ylab = resargs['ylabel']
rg.disp_getargs(resargs)
histbins = resargs['histbins']
colourhist = resargs['colourhist']
histxlab = resargs['histxlab']
histylab = resargs['histylab']
histtitle = resargs['histtitle']
addsk = resargs['addsk']

if min(percentiles) <= 0.0:
    print("Minimum percentiles must be >0", file=sys.stderr)
    sys.exit(2)
if max(percentiles) >= 100.0:
    print("Maximum percentiles must be <100", file=sys.stderr)
    sys.exit(3)

percentiles += [0, 100]
colours = 255 - np.round(2.0 ** np.linspace(0, 8, len(percentiles) - 1) - 1.0).astype(np.int32)

percentiles.sort()

nfigs = len(files)
fignum = 1

if figout is not None:
    figout = miscutils.removesuffix(figout, '.png')

plt.rc('figure', max_open_warning=100)
# Get details of object once only if doing multiple pictures

for file in files:

    ff = fits.open(file)
    hdr = ff[0].header
    dat = trimarrays.trimzeros(trimarrays.trimnan(ff[0].data.astype(np.float64)))
    
    try:
        date = Time(hdr['DATE-OBS'])
        when = date.datetime
    except KeyError:
        date = None
    
    plotfigure = rg.plt_figure()
    plotfigure.canvas.set_window_title('FITS Image from file ' + file)
    plt.subplot(121)

    crange = np.percentile(dat, percentiles)
    collist = ["#%.2x%.2x%.2x" % (i, i, i) for i in colours]
    cmap = colors.ListedColormap(collist)
    norm = colors.BoundaryNorm(crange, cmap.N)
    img = plt.imshow(dat, cmap=cmap, norm=norm, origin='lower')
    plt.colorbar(img, norm=norm, cmap=cmap, boundaries=crange, ticks=crange)      

    tit = title
    if date is not None:
        tit += date.datetime.strftime("\nfor file date  %d/%m/%Y @ %H:%M:%S")
    plt.title(tit)
    plt.xlabel(xlab)
    plt.ylabel(ylab)
    plt.subplot(122)
    
    flatdat = dat.flatten()
    mv = flatdat.mean()
    flatdat /= mv
    plt.hist(flatdat, bins=histbins, color=colourhist)
    plt.xlabel(histxlab)
    plt.ylabel(histylab)
    
    tit = histtitle
    if  addsk:
        tit += " of %.6g\nMedian=%.6g Std dev=%.4g\nSkew=%.4g Kurtosis %.4g" % (mv, np.median(flatdat), flatdat.std(), ss.skew(flatdat), ss.kurtosis(flatdat))
    plt.title(tit)

    if figout is not None:
        if nfigs > 1:
            outfile = figout + "%.3d" % fignum + ".png"
            fignum += 1
        else:
            outfile = figout + ".png"
        plotfigure.savefig(outfile)
        plt.close(plotfigure)

if figout is None:
    plt.show()
