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
import dbobjinfo
import remgeom
import dbremfitsobj
import dbops
import remdefaults
import strreplace

parsearg = argparse.ArgumentParser(description='Display images from database', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('obsinds', type=int, nargs='+', help='Observation ids to display')
parsearg.add_argument('--database', type=str, default=remdefaults.default_database(), help='Database to use')
parsearg.add_argument('--figout', type=str, help='File to output figure(s) to')
parsearg.add_argument('--percentiles', type=int, default=4, help="Number of percentiles to divide greyscale into")
parsearg.add_argument('--biasvalue', type=float, help='Use this value instead of bias"')
parsearg.add_argument('--biasid', type=int, help='ID of image to use for bias')
parsearg.add_argument('--replstd', type=float, default=5.0, help='Replace exceptional values > this with median')
parsearg.add_argument('--invert', action='store_false', help='Invert image')
parsearg.add_argument('--divisions', type=int, default=8, help='Divisions in RA/Dec lines')
parsearg.add_argument('--divprec', type=int, default=3, help='Precision for axes')
parsearg.add_argument('--pstart', type=int, default=1, help='2**-n fraction to start display at')
parsearg.add_argument('--divthresh', type=int, default=15, help='Pixels from edge for displaying divisions')
parsearg.add_argument('--racolour', type=str, help='Colour of RA lines')
parsearg.add_argument('--deccolour', type=str, help='Colour of DEC lines')
parsearg.add_argument('--targcolour', type=str, default='#44FF44', help='Target object colour')
parsearg.add_argument('--objcolour', type=str, default='cyan', help='Other Object colour')
parsearg.add_argument('--hilalpha', type=float, default=1.0, help='Object alpha')
parsearg.add_argument('--trim', action='store_true', help='Trim trailing empty pixels')
parsearg.add_argument('--mainap', type=int, default=6, help='main aperture radius')

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

dbname = resargs['database']
obsinds = resargs['obsinds']
figout = resargs['figout']
percentiles = resargs['percentiles']

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

targcolour = resargs['targcolour']
objcolour = resargs['objcolour']
hilalpha  = resargs['hilalpha']
trimem = resargs['trim']
mainap = resargs['mainap']
biasvalue= resargs['biasvalue']
biasid = resargs['biasid']
replstd = resargs['replstd']

dbase = dbops.opendb(dbname)
dbcurs = dbase.cursor()

nfigs = len(obsinds)
fignum = 1

if figout is not None:
    figout = miscutils.removesuffix(figout, '.png')

setbtab = None
if biasid is not None:
    bf = dbremfitsobj.getfits(dbcurs, biasid)
    setbtab = bf[0].data.astype(np.float64)
    bf.close()

# Get details of object once only if doing multiple pictures

objlookup = dict()

for obsind in obsinds:

    nfnd = dbcurs.execute("SELECT object,date_obs,filter,ind FROM obsinf WHERE obsind=" + str(obsind))

    if nfnd == 0:
        print("Unknown obs ind", obsind, file=sys.stderr)
        continue

    rows = dbcurs.fetchall()
    target, when, filter, fitsind = rows[0]

    if filter not in 'grizHJK' and filter != 'GRI':
        print("obsid", obsind, "on", when.strftime("%d/%M/%Y"), "for target", target,  "has unsupported filter", filter, file=sys.stderr)
        continue
    
    if fitsind == 0:
        print("obsid", obsind, "on", when.strftime("%d/%M/%Y"), "for target", target, "filter", filter, "has no fits file", file=sys.stderr)
        continue

    # Get definitive name

    target = dbobjinfo.get_targetname(dbcurs, target)

    # Get appropriate flat/bias files

    if filter in 'griz':

        flattab, biastab = dbremfitsobj.get_nearest_forbinf(dbcurs, when.year, when.month)

        ftab = flattab[filter]
        btab = biastab[filter]

        ff = dbremfitsobj.getfits(dbcurs, ftab.fitsind)
        fdat = trimarrays.trimzeros(trimarrays.trimnan(ff[0].data))
        ffrows, ffcols = fdat.shape
        ff.close()
        
        ffile = dbremfitsobj.getfits(dbcurs, fitsind)
        ffhdr = ffile[0].header
        imagedata = ffile[0].data.astype(np.float64)
        ffile.close()

        if biasvalue is not None:
            bdat = np.full_like(imagedata, biasvalue)
        elif setbtab is not None:
            bdat = setbtab.copy()
        else:
            bf = dbremfitsobj.getfits(dbcurs, btab.fitsind)
            bdat = bf[0].data.astype(np.float64)
            bf.close()
        
        # Get actual image data
        
        (imagedata, bdatc) = trimarrays.trimto(fdat, imagedata, bdat)
        
        if replstd > 0.0:
           bdatc = strreplace.strreplace(bdatc, replstd)
        
        # Extra stuff
        
        #fdat -= bdatc
        #print("Minimum flat =", fdat.min())
        
        imagedata -= bdatc
        #imagedata *= fdat.mean()
        imagedata /= fdat

    else:
        ffile = dbremfitsobj.getfits(dbcurs, fitsind)
        ffhdr = ffile[0].header
        imagedata = ffile[0].data.astype(np.float64)
        ffile.close()

    w = wcscoord.wcscoord(ffhdr)

    if rg.trims.bottom is not None:
        imagedata = imagedata[rg.trims.bottom:]
        w.set_offsets(yoffset=rg.trims.bottom)

    if rg.trims.left is not None:
        imagedata = imagedata[:,rg.trims.left:]
        w.set_offsets(xoffset=rg.trims.left)

    if rg.trims.right is not None:
        imagedata = imagedata[:,0:-rg.trims.right]

    plotfigure = plt.figure(figsize=(rg.width, rg.height))
    plotfigure.canvas.set_window_title('FITS Image obsind %d' % obsind)

    med = np.median(imagedata)
    sigma = imagedata.std()
    mx = imagedata.max()
    mn = imagedata.min()
    fi = imagedata.flatten()
    pcs = np.linspace(0, 100, percentiles+1)
    crange = np.percentile(imagedata, pcs)
    mapsize = crange.shape[0]-1
    cl = np.linspace(0, 255, mapsize, dtype=int)
    if invertim:
        cl = 255 - cl
    collist = ["#%.2x%.2x%.2x" % (i,i,i) for i in cl]
    cmap = colors.ListedColormap(collist)
    norm = colors.BoundaryNorm(crange, cmap.N)
    img = plt.imshow(imagedata, cmap=cmap, norm=norm, origin='lower')
    plt.colorbar(img, norm=norm, cmap=cmap, boundaries=crange, ticks=crange)

    # OK get coords of edges of picture

    pixrows, pixcols = imagedata.shape
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

    labax = plotax = plt.gca()

    nfnd, nnfnd = dbremfitsobj.get_find_results(dbcurs, obsind)

    if nfnd > 0:
        dbcurs.execute("SELECT objname,pixcol,pixrow,radeg,decdeg FROM identobj WHERE obsind=" + str(obsind))
        objrows = dbcurs.fetchall()
        nobj = len(objrows) - 1
        for objname, pixcol, pixrow, radeg, decdeg in objrows:
            try:
                objdets = objlookup[objname]
            except KeyError:
                objdets = dbobjinfo.get_object(dbcurs, objname)
                objlookup[objname] = objdets
            tcoords = w.relpix((pixcol, pixrow))
            trad = objdets.get_aperture(mainap)
            colour = objcolour
            if objname == target:
                colour = targcolour
            ptch = mp.Circle(tcoords, radius=trad, alpha=hilalpha, color=colour, fill=False)
            plotax.add_patch(ptch)
        tit = when.strftime("%Y-%m-%d %H:%M:%S") + " filter " + filter + " target " + target + "," + str(nobj) + " objs found"

    elif nnfnd > 0:
        dbcurs.execute("SELECT comment FROM notfound WHERE obsind=" + str(obsind))
        objrows = dbcurs.fetchall()
        tit = when.strftime("%Y-%m-%d %H:%M:%S") + " filter " + filter + " target " + target + "," + objrows[0][0]

    else:
        tit = when.strftime("%Y-%m-%d %H:%M:%S") + " filter " + filter + " target " + target + " (unprocessed)"

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
