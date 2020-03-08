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
import matplotlib.patches as mp
from matplotlib import colors
import argparse
import sys
import datetime
import os.path
import objcoord
import trimarrays
import wcscoord
import warnings
import miscutils
import remgeom
import strreplace
import findfast
import radecgridplt
from astropy._erfa.core import apcs

rg = remgeom.load()

parsearg = argparse.ArgumentParser(description='Display image files', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', type=str, nargs='+', help='File names to display')
parsearg.add_argument('--grayscale', type=str, required=True, help="Standard grayscale to use")
parsearg.add_argument('--title', type=str, help='Optional title to put at head of image')
parsearg.add_argument('--biasfile', type=str, help='Bias file to apply')
parsearg.add_argument('--flatfile', type=str, help='Flat file to apply')
parsearg.add_argument('--replstd', type=float, default=5.0, help='Replace exceptional values > this with median')
parsearg.add_argument('--mainap', type=int, default=6, help='main aperture radius')
parsearg.add_argument('--searchstd', type=float, default=10, help='Nnumber of std deviations to search from')
parsearg.add_argument('--maxobjs', type=int, default=10, help='Maximum number of objects to display"')

rg.disp_argparse(parsearg)

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

figout = rg.disp_getargs(resargs)

biasfile = resargs['biasfile']
flatfile = resargs['flatfile']
grayscalename = resargs['grayscale']
replstd = resargs['replstd']
mainap = resargs['mainap']
searchstd = resargs['searchstd']
maxobjs = resargs['maxobjs']
title = resargs['title']

gsdets = rg.get_grayscale(grayscalename)
if gsdets is None:
    print("Sorry gray scale", grayscalename, "is not defined", file=sys.stderr)
    sys.exit(9)

collist = gsdets.get_colours()
cmap = colors.ListedColormap(collist)

# if rg.divspec.invertim:
#    collist = [p for p in reversed(collist)]
# percentiles.sort()

nfigs = len(files)
fignum = 1

if figout is not None:
    figout = miscutils.removesuffix(figout, '.png')

fdat = None
if flatfile is not None:
    ffile = fits.open(flatfile)
    fdat = trimarrays.trimzeros(trimarrays.trimnan(ffile[0].data))
    ffile.close()

bdat = None
if biasfile is not None:
    bfile = fits.open(biasfile)
    bhdr = bfile[0].header
    try:
        etime = bhdr['EXPTIME']
        if etime != 0:
            print(biasfile, "does not look like a bias file, exptime is", etime, file=sys.stderr)
            sys.exit(20)
    except KeyError:
        pass
    bdat = bfile[0].data.astype(np.float64)
    bfile.close()
    if fdat is not None:
        (bdat,) = trimarrays.trimto(fdat, bdat)
    if replstd > 0.0:
        bdat = strreplace.strreplace(bdat, replstd)

# Get details of object once only if doing multiple pictures

for file in files:

    ff = fits.open(file)
    hdr = ff[0].header
    dat = ff[0].data.astype(np.float64)
    if fdat is not None:
        (dat,) = trimarrays.trimto(fdat, dat)
    if bdat is not None:
        dat -= bdat
    if fdat is not None:
        dat /= fdat

    try:
        target = hdr['OBJECT']
    except KeyError:
        target = "(None)"

    try:
        date = Time(hdr['DATE-OBS'])
        when = date.datetime
    except KeyError:
        date = None

    w = wcscoord.wcscoord(hdr)
    (dat,) = rg.apply_trims(w, dat)

    plotfigure = rg.plt_figure()
    plotfigure.canvas.set_window_title('FITS Image from file ' + file)

    med = np.median(dat)
    sigma = dat.std()
    mx = dat.max()
    mn = dat.min()
    fi = dat.flatten()
    crange = gsdets.get_cmap(dat)
    norm = colors.BoundaryNorm(crange, cmap.N)
    img = plt.imshow(dat, cmap=cmap, norm=norm, origin='lower')
    plt.colorbar(img, norm=norm, cmap=cmap, boundaries=crange, ticks=crange)

    radecgridplt.radecgridplt(w, dat, rg)

    objlist = None
    if searchstd > 0:
        objlist = findfast.findfast(dat, searchstd, mainap)
        n = 0
        labchr = 65
        for r, c, adus in objlist:
            tcoords = (c, r)
            objc = rg.objdisp.objcolour[n % len(rg.objdisp.objcolour)]
            ptch = mp.Circle(tcoords, radius=mainap, alpha=rg.objdisp.objalpha, color=objc, fill=rg.objdisp.objfill)
            plt.gca().add_patch(ptch)
            displ = tcoords[0] + rg.objdisp.objtextdisp
            if displ >= dat.shape[0]:
                displ = tcoords[0] - rg.objdisp.objtextdisp
            plt.text(displ, tcoords[1], chr(labchr), fontsize=rg.objdisp.objtextfs, color=objc)
            n += 1
            if n >= maxobjs:
                break
            labchr += 1
            if labchr > 122:
                labchr = 65
            elif labchr == 91:
                labchr = 97

    if date is None:
        tit = "Target: " + target + " (no date)"
    else:
        tit = "Target: " + target + when.strftime(" %Y-%m-%d %H:%M:%S")

    if objlist is not None:
         tit += " " + str(len(objlist)) + " objects found"

    if title is not None:
        tit = title + "\n" + tit

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
