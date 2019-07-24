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
from _curses import nocbreak

parsearg = argparse.ArgumentParser(description='Display image files', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', type=str, nargs='+', help='File names to display')
parsearg.add_argument('--figout', type=str, help='File to output figure(s) to')
parsearg.add_argument('--percentiles', type=int, default=4, help="Number of percentiles to divide greyscale into")
parsearg.add_argument('--biasfile', type=str, help='Bias file to apply')
parsearg.add_argument('--flatfile', type=str, help='Flat file to apply')
parsearg.add_argument('--replstd', type=float, default=5.0, help='Replace exceptional values > this with median')
parsearg.add_argument('--invert', action='store_false', help='Invert image')
parsearg.add_argument('--divisions', type=int, default=8, help='Divisions in RA/Dec lines')
parsearg.add_argument('--divprec', type=int, default=3, help='Precision for axes')
parsearg.add_argument('--pstart', type=int, default=1, help='2**-n fraction to start display at')
parsearg.add_argument('--divthresh', type=int, default=15, help='Pixels from edge for displaying divisions')
parsearg.add_argument('--racolour', type=str, help='Colour of RA lines')
parsearg.add_argument('--deccolour', type=str, help='Colour of DEC lines')
parsearg.add_argument('--trim', action='store_true', help='Trim trailing empty pixels')
parsearg.add_argument('--nocoords', action='store_true', help='Suppress coord display')

resargs = vars(parsearg.parse_args())

rg = remgeom.load()

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
biasfile = resargs['biasfile']
flatfile = resargs['flatfile']

invertim = resargs['invert']
divisions = resargs['divisions']
divprec = resargs['divprec']
pstart = resargs['pstart']
divthresh = resargs['divthresh']
racol=resargs['racolour']
deccol=resargs['deccolour']
if invertim:
    if racol is None:
        racol = "#771111"
    if deccol is None:
        deccol = "#1111AA"
else:
    if racol is None:
        racol = "#FFCCCC"
    if deccol is None:
        deccol = "#CCCCFF"

trimem = resargs['trim']
replstd = resargs['replstd']
nocoords = resargs['nocoords']

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
        (bdat, ) = trimarrays.trimto(fdat, bdat)   
    if replstd > 0.0:
        bdat = strreplace.strreplace(bdat, replstd)

# Get details of object once only if doing multiple pictures

for file in files:

    ff = fits.open(file)
    hdr = ff[0].header
    dat = ff[0].data.astype(np.float64)
    if fdat is not None:
        (dat, )  = trimarrays.trimto(fdat, dat)
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

    if rg.trims.bottom is not None:
        dat = dat[rg.trims.bottom:]
        w.set_offsets(yoffset=rg.trims.bottom)

    if rg.trims.left is not None:
        dat = dat[:,rg.trims.left:]
        w.set_offsets(xoffset=rg.trims.left)

    if rg.trims.right is not None and rg.trims.right != 0:
        dat = dat[:,0:-rg.trims.right]

    plotfigure = plt.figure(figsize=(rg.width, rg.height))
    plotfigure.canvas.set_window_title('FITS Image from file ' + file)

    med = np.median(dat)
    sigma = dat.std()
    mx = dat.max()
    mn = dat.min()
    fi = dat.flatten()
    pcs = np.linspace(0, 100, percentiles+1)
    crange = np.percentile(dat, pcs)
    mapsize = crange.shape[0]-1
    cl = np.linspace(0, 255, mapsize, dtype=int)
    if invertim:
        cl = 255 - cl
    collist = ["#%.2x%.2x%.2x" % (i,i,i) for i in cl]
    cmap = colors.ListedColormap(collist)
    norm = colors.BoundaryNorm(crange, cmap.N)
    img = plt.imshow(dat, cmap=cmap, norm=norm, origin='lower')
    plt.colorbar(img, norm=norm, cmap=cmap, boundaries=crange, ticks=crange)

    if not nocoords:
        
        # OK get coords of edges of picture

        pixrows, pixcols = dat.shape
        cornerpix = ((0,0), (pixcols-1, 0), (9, pixrows-1), (pixcols-1, pixrows-1))
        cornerradec = w.pix_to_coords(cornerpix)
        isrotated = abs(cornerradec[0,0] - cornerradec[1,0]) < abs(cornerradec[0,0] - cornerradec[2,0])

        # Get matrix of ra/dec each pixel

        pixarray = np.array([[(x, y) for x in range(0, pixcols)] for y in range(0, pixrows)])
        pixcoords = w.pix_to_coords(pixarray.reshape(pixrows*pixcols,2)).reshape(pixrows,pixcols,2)
        ratable = pixcoords[:,:,0]
        dectable = pixcoords[:,:,1]
        ramax, decmax = cornerradec.max(axis=0)
        ramin, decmin = cornerradec.min(axis=0)

        radivs = np.linspace(ramin, ramax, divisions).round(divprec)
        decdivs = np.linspace(decmin, decmax, divisions).round(divprec)

        ra_x4miny = []
        ra_y4minx = []
        ra_xvals = []
        ra_yvals = []
        dec_x4miny = []
        dec_y4minx = []
        dec_xvals = []
        dec_yvals = []

        for r in radivs:
            ra_y = np.arange(0, pixrows)
            diffs = np.abs(ratable-r)
            ra_x = diffs.argmin(axis=1)
            sel = (ra_x > 0) & (ra_x < pixcols-1)
            ra_x = ra_x[sel]
            ra_y = ra_y[sel]
            if len(ra_x) == 0: continue
            if ra_y[0] < divthresh:
                ra_x4miny.append(ra_x[0])
                ra_xvals.append(r)
            if ra_x.min() < divthresh:
                ra_y4minx.append(ra_y[ra_x.argmin()])
                ra_yvals.append(r)
            plt.plot(ra_x, ra_y, color=racol, alpha=0.5)

        for d in decdivs:
            dec_x = np.arange(0, pixcols)
            diffs = np.abs(dectable-d)
            dec_y = diffs.argmin(axis=0)
            sel = (dec_y > 0) & (dec_y < pixrows-1)
            dec_x = dec_x[sel]
            dec_y = dec_y[sel]
            if len(dec_x) == 0: continue
            if dec_x[0] < divthresh:
                dec_y4minx.append(dec_y[0])
                dec_yvals.append(d)
            if dec_y.min() < divthresh:
                dec_x4miny.append(dec_x[dec_y.argmin()])
                dec_xvals.append(d)
            plt.plot(dec_x, dec_y, color=deccol, alpha=0.5)

        fmt = '%.' + str(divprec) + 'f'

        if isrotated:
            rafmt = [fmt % r for r in ra_yvals]
            decfmt = [fmt % d for d in dec_xvals]
            plt.yticks(ra_y4minx, rafmt)
            plt.xticks(dec_x4miny, decfmt)
            plt.ylabel('RA (deg)')
            plt.xlabel('Dec (deg)')
        else:
            rafmt = [fmt % r for r in ra_xvals]
            decfmt = [fmt % d for d in dec_yvals]
            plt.xticks(ra_x4miny, rafmt)
            plt.yticks(dec_y4minx, decfmt)
            plt.xlabel('RA (deg)')
            plt.ylabel('Dec (deg)')

    if date is None:
        tit = "Target: " + target + " (no date)"
    else:
        tit = "Target: " + target + when.strftime(" %Y-%m-%d %H:%M:%S") 

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
