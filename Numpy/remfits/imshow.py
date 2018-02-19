#! /usr/bin/env python

from astropy.io import fits
from astropy import wcs
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
import astroquery.utils as autils
import matplotlib.pyplot as plt
import matplotlib.patches as mp
from matplotlib import colors 
import numpy as np
import argparse
import sys
import string
import objcoord
import findimagelocs
import warnings
import miscutils

parsearg = argparse.ArgumentParser(description='Plot FITS image', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('file', type=str, nargs=1, help='FITS file to plot can be compressed')
parsearg.add_argument('--cutoff', type=float, help='Reduce maxima to this value', default=-1.0)
parsearg.add_argument('--trim', action='store_true', help='Trim trailing empty pixels')
parsearg.add_argument('--mapsize', type=int, default=8, help='Number of shades in grey scale')
parsearg.add_argument('--divisions', type=int, default=8, help='Divisions in RA/Dec lines')
parsearg.add_argument('--divprec', type=int, default=3, help='Precision for axes')
parsearg.add_argument('--pstart', type=int, default=4, help='2**-n fraction to start display at')
parsearg.add_argument('--divthresh', type=int, default=15, help='Pixels from edge for displaying divisions')
parsearg.add_argument('--racolour', type=str, default='#FFCCCC', help='Colour of RA lines')
parsearg.add_argument('--deccolour', type=str, default='#CCCCFF', help='Colour of DEC lines')
parsearg.add_argument('--apsize', type=int, default=6, help='aperture radius')
parsearg.add_argument('--aduthresh', type=float, default=20000.0, help='Number of ADUs to select objects for')
parsearg.add_argument('--hilcolour', type=str, default='r', help='Object colour')
parsearg.add_argument('--hilalpha', type=float, default=0.75, help='Object alpha')
parsearg.add_argument('--objrad', type=float, default=1.0, help='Object search radius in arcmin')
parsearg.add_argument('--laboffset', type=int, default=5, help='Offset in pixels to put text in')
parsearg.add_argument('--labcolour', type=str, default='#BBFFBB', help='Colour of labels')
parsearg.add_argument('--minpix', type=int, default=10, help='Minimum pixels from the edge for object coords')
parsearg.add_argument('--outcoords', type=str, help='File to output coordingates found')
parsearg.add_argument('--figout', type=str, help='File to putput figure to')
parsearg.add_argument('--splitfig', action='store_true', help='Put identified stars in separate figure')

resargs = vars(parsearg.parse_args())
ffname = resargs['file'][0]

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)
autils.suppress_vo_warnings()
ffile = fits.open(ffname)
ffhdr = ffile[0].header
cutoff = resargs['cutoff']
trimem = resargs['trim']
mapsize = resargs['mapsize']
divisions = resargs['divisions']
divprec = resargs['divprec']
pstart = resargs['pstart']
divthresh = resargs['divthresh']
racol=resargs['racolour']
deccol=resargs['deccolour']
figout = resargs['figout']

apsize = resargs['apsize']
aduthresh = resargs['aduthresh']
hilcolour = resargs['hilcolour']
hilalpha = resargs['hilalpha']
objrad = resargs['objrad']
laboffset = resargs['laboffset']
labcolour = resargs['labcolour']
outcoords = resargs['outcoords']
minpix = resargs['minpix']

splitfig = resargs['splitfig']

imagedata = ffile[0].data

if trimem:
    while np.count_nonzero(imagedata[-1]) == 0:
        imagedata = imagedata[0:-1]

    while np.count_nonzero(imagedata[:,-1]) == 0:
        imagedata = imagedata[:,0:-1]

imagedata = imagedata + 0.0

if cutoff > 0.0:
    imagedata = np.clip(imagedata, None, cutoff)

plotfigure = plt.figure(figsize=(10,12))
if splitfig:
    plotfigure.canvas.set_window_title('Image only')
else:
    plotfigure.canvas.set_window_title('Image wutg narjed stars')

med = np.median(imagedata)
mx = imagedata.max()
fi = imagedata.flatten()
fi = fi[fi > med]
pcs = 100.0*(1.0-2.0**-np.arange(pstart,mapsize+pstart-1))
crange = np.concatenate(((0.0,), np.percentile(fi, pcs), (mx,)))
cl=np.log10(np.logspace(1, 256, mapsize)).round()-1
collist = ["#%.2x%.2x%.2x" % (i,i,i) for i in cl]
cmap = colors.ListedColormap(collist)
norm = colors.BoundaryNorm(crange, cmap.N)
img = plt.imshow(imagedata, cmap=cmap, norm=norm, origin='lower')
plt.colorbar(img, norm=norm, cmap=cmap, boundaries=crange, ticks=crange)

# OK get coords of edges of picture

pixrows, pixcols = imagedata.shape
#devnull = open('/dev/null', 'w')

#sys.stderr = devnull
w = wcs.WCS(ffhdr)
#sys.stderr = sys.__stderr__

cornerpix = np.array(((0,0), (pixcols-1, 0), (0, pixrows-1), (pixcols-1, pixrows-1)), np.float)

cornerradec = w.wcs_pix2world(cornerpix, 0)
isrotated = abs(cornerradec[0,0] - cornerradec[1,0]) < abs(cornerradec[0,0] - cornerradec[2,0])

# Get matrix of ra/dec each pixel

pixarray = np.array([[(x,y) for x in range(0,pixcols)] for y in range(0,pixrows)])
pixcoords = w.wcs_pix2world(pixarray.reshape(pixrows*pixcols,2), 0).reshape(pixrows,pixcols,2)
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

if splitfig:
    xls = plotax.get_xlim()
    yls = plotax.get_ylim()
    labfigure = plt.figure(figsize=(10,12))
    labfigure.canvas.set_window_title('Key stars')
    labax = plt.gca()
    plt.xlim(xls)
    plt.ylim(yls)

objlist = findimagelocs.findimagelocs(imagedata - med, aduthresh, apsize)
if minpix != 0:
    sel = []
    for row in objlist:
        sel.append((row[0] >= minpix) & (row[0] < minpix + pixcols) & (row[1] >= minpix) & (row[1] < minpix + pixrows))
    objlist = objlist[sel]
if len(objlist) != 0:
    objpix = [(x,y) for x,y,a in objlist]
    objradec = w.wcs_pix2world(objpix, 0)
    if  outcoords is not None:
        np.savetxt(outcoords, objradec)

for ob in objlist:
    bcol, brow, dau = ob
    ptch = mp.Circle((bcol,brow), radius=apsize, alpha=hilalpha,color=hilcolour, fill=False)
    labax.add_patch(ptch)
    tcra, tcdec = w.wcs_pix2world(((bcol, brow),), 0).flatten()
    objnames = objcoord.coord2objs(tcra, tcdec, objrad)
    if len(objnames) != 0:
        lab = objnames[0]
    else:
        lab = "(%.4f %.4f)" % (tcra, tcdec)
    lcol = bcol + laboffset
    if float(lcol)/float(pixcols) > 0.9:
        lcol = max(bcol - laboffset, 0)
    lrow = brow + laboffset
    if float(lrow)/float(pixrows) > 0.9:
         lrow = max(brow - laboffset, 0)
    labax.text(lcol, lrow, lab, color=labcolour)

odt = 'Unknown date'
for dfld in ('DATE-OBS', 'DATE', '_ATE'):
    if dfld in ffhdr:
        odt = ffhdr[dfld]
        break

tit = ffhdr['OBJECT'] + ' on ' + string.replace(odt, 'T', ' at ') + ' filter ' + ffhdr['FILTER']
plt.title(tit)
if splitfig:
    plotax.set_title(tit)
if figout is None:
    plt.show()
else:
    figout = miscutils.removesuffix(figout, 'png')
    if splitfig:
        plotfigure.savefig(figout + '_plot.png')
        labfigure.savefig(figout + '_lab.png')
    else:
        plotfigure.savefig(figout + '.png')

