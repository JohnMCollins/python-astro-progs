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
import re
import datetime
import os.path
import trimarrays
import warnings
import miscutils
import strreplace
import remgeom

filtfn = dict(BL='z', BR="r", UR="g", UL="i")
revfilt = dict()
for k, v in filtfn.items():
    revfilt[v] = k

qfilt = 'zrig'

fmtch = re.compile('([FBIm]).*([UB][LR])')
ftypes = dict(F='Daily flat', B='Daily bias', I='Image', m='Master')

rg = remgeom.load()

parsearg = argparse.ArgumentParser(description='Display image files raw', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', type=str, nargs='+', help='File names to display')
parsearg.add_argument('--title', type=str, default="Image display", help="Title for each plot")
parsearg.add_argument('--xlabel', type=str, default="Column number", help="X xxis label")
parsearg.add_argument('--ylabel', type=str, default="Row number", help="Y xxis label")
parsearg.add_argument('--grayscale', type=str, required=True, help="Standard grayscale to use")
parsearg.add_argument('--histbins', type=int, default=20, help='Bins for histogram')
parsearg.add_argument('--logscale', action='store_true', help='Use log scale for histogram')
parsearg.add_argument('--colourhist', type=str, default='b', help='Colour of historgram')
parsearg.add_argument('--histtitle', type=str, default='Distribution normalised to mean', help='Histogram Title')
parsearg.add_argument('--histxlab', type=str, default='Pixel value normalised to mean', help='Label for histogram X axis')
parsearg.add_argument('--histylab', type=str, default='Occurences of vaalue', help='Label for histogram Y axis')
parsearg.add_argument('--addsk', action='store_false', help='Add stats to histogram title')
rg.disp_argparse(parsearg, "dwin")

resargs = vars(parsearg.parse_args())

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)
autils.suppress_vo_warnings()

grayscalename = resargs['grayscale']
files = resargs['files']
logscale = resargs['logscale']
title = resargs['title']
xlab = resargs['xlabel']
ylab = resargs['ylabel']
figout = rg.disp_getargs(resargs)
histbins = resargs['histbins']
colourhist = resargs['colourhist']
histxlab = resargs['histxlab']
histylab = resargs['histylab']
histtitle = resargs['histtitle']
addsk = resargs['addsk']

gsdets = rg.get_grayscale(grayscalename)
if gsdets is None:
    print("Sorry gray scale", grayscalename, "is not defined", file=sys.stderr)
    sys.exit(9)

collist = gsdets.get_colours()
cmap = colors.ListedColormap(collist)

nfigs = len(files)
fignum = 1

if figout is not None:
    figout = miscutils.removesuffix(figout, '.png')

plt.rc('figure', max_open_warning=100)
# Get details of object once only if doing multiple pictures

for file in files:

    try:
        ff = fits.open(file)
    except OSError as e:
        print("Cannot open", file, e.strerror, file=sys.stderr)
        continue
    hdr = ff[0].header
    dat = trimarrays.trimzeros(trimarrays.trimnan(ff[0].data.astype(np.float64)))

    try:
        date = Time(hdr['DATE-OBS'])
        when = date.datetime
    except KeyError:
        date = None

    filter = None
    try:
        filter = hdr['FILTER']
    except KeyError:
        pass

    ftype = 'Unknown"'
    try:
        intfname = hdr['FILENAME']
        fm = fmtch.match(intfname)
        if fm:
            ftp, quad = fm.groups()
            ffilt = filtfn[quad]
            if filter is None:
                filter = ffilt
            elif ffilt != filter:
                print("Odd filter type", filter, "in", file, "int file", intfname, "which suggests filter", ffilt, file=sys.stderr)
                continue
            ftype = ftypes[ftp]
        else:
            ftype = "Generated " + intfname
    except KeyError:
        pass

    if filter is None:
        filter = "(unknown)"

    plotfigure = rg.plt_figure()
    plotfigure.canvas.set_window_title('FITS Image from file ' + file)
    plt.subplot(121)

    crange = gsdets.get_cmap(dat)
    norm = colors.BoundaryNorm(crange, cmap.N)
    img = plt.imshow(dat, cmap=cmap, norm=norm, origin='lower')
    plt.colorbar(img, norm=norm, cmap=cmap, boundaries=crange, ticks=crange)

    tit = title
    if date is not None:
        tit += "\nfor " + ftype + " file filter " + filter + "\n" + date.datetime.strftime("Date %d/%m/%Y @ %H:%M:%S")
    plt.title(tit)
    plt.xlabel(xlab)
    plt.ylabel(ylab)
    plt.subplot(122)

    flatdat = dat.flatten()
    mv = flatdat.mean()
    flatdat /= mv
    plt.hist(flatdat, bins=histbins, color=colourhist, log=logscale)
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
