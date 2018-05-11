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
import trimarrays
import wcscoord
import warnings
import miscutils
import objinfo
import findnearest

parsearg = argparse.ArgumentParser(description='Plot FITS image', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('file', type=str, nargs=1, help='FITS file to plot can be compressed')
parsearg.add_argument('--libfile', type=str, default='~/lib/stellar_data', help='File to use for database')
parsearg.add_argument('--cutoff', type=float, help='Reduce maxima to this value', default=-1.0)
parsearg.add_argument('--trim', action='store_true', help='Trim trailing empty pixels')
parsearg.add_argument('--mapsize', type=int, default=8, help='Number of shades in grey scale')
parsearg.add_argument('--invert', action='store_true', help='Invert image')
parsearg.add_argument('--divisions', type=int, default=8, help='Divisions in RA/Dec lines')
parsearg.add_argument('--divprec', type=int, default=3, help='Precision for axes')
parsearg.add_argument('--pstart', type=int, default=4, help='2**-n fraction to start display at')
parsearg.add_argument('--divthresh', type=int, default=15, help='Pixels from edge for displaying divisions')
parsearg.add_argument('--racolour', type=str, help='Colour of RA lines')
parsearg.add_argument('--deccolour', type=str, help='Colour of DEC lines')
parsearg.add_argument('--figout', type=str, help='File to putput figure to')
parsearg.add_argument('--flatfile', type=str, help='Flat file to use')
parsearg.add_argument('--biasfile', type=str, help='Bias file to use')
parsearg.add_argument('--trimbottom', type=int, help='Pixels to trim off bottom of picture')
parsearg.add_argument('--trimleft', type=int, help='Pixels to trim off left of picture')
parsearg.add_argument('--trimright', type=int, help='Pixels to trim off right of picture')
parsearg.add_argument('--searchrad', type=int, default=20, help='Search radius in pixels')
parsearg.add_argument('--target', type=str, help='Name of target')
parsearg.add_argument('--mainap', type=int, default=6, help='main aperture radius')
parsearg.add_argument('--targcolour', type=str, default='r', help='Target object colour')
parsearg.add_argument('--objcolour', type=str, default='yellow', help='Other Object colour')
parsearg.add_argument('--hilalpha', type=float, default=0.75, help='Object alpha')

resargs = vars(parsearg.parse_args())
ffname = resargs['file'][0]

libfile = os.path.expanduser(resargs['libfile'])

objinf = objinfo.ObjInfo()
try:
    objinf.loadfile(libfile)
except objinfo.ObjInfoError as e:
    if e.warningonly:
        print  >>sys.stderr, "(Warning) file does not exist:", libfile
    else:
        print >>sys.stderr,  "Error loading file", e.args[0]
        sys.exit(30)

# The reason why we don't get RA and DECL info out of this is because we have
# to adjust for proper motion which requires Python 3 (as the versions of astropy that
# support it only run with that)

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)
autils.suppress_vo_warnings()

ffile = fits.open(ffname)
ffhdr = ffile[0].header

cutoff = resargs['cutoff']
trimem = resargs['trim']
mapsize = resargs['mapsize']
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

figout = resargs['figout']
flatfile = resargs['flatfile']
biasfile = resargs['biasfile']

trimbottom = resargs['trimbottom']
trimleft = resargs['trimleft']
trimright = resargs['trimright']

searchrad = resargs['searchrad']
objfile = resargs['objfile']
target = resargs['target']
if target is not None:
    try:
        target = objinf.get_main(target)
    except objinfo.ObjInfoError as e:
        print >>sys.stderr, e.args[0]
        sys.exit(30)
mainap = resargs['mainap']
targcolour = resargs['targcolour']
objcolour = resargs['objcolour']
hilalpha  = resargs['hilalpha']

if flatfile is not None:
    ff = fits.open(flatfile)
    fdat = trimarrays.trimnan(ff[0].data)
    ffrows, ffcols = fdat.shape

imagedata = ffile[0].data.astype(np.float64)

if biasfile is not None:
    bf = fits.open(biasfile)
    bdat = bf[0].data
    if flatfile is not None:
        bdat = bdat[0:ffrows,0:ffcols]
    bdat = bdat.astype(np.float64)
else:
    bdat = np.zeros_like(imagedata)

if flatfile is not None:
    imagedata, bdat = trimarrays.trimto(fdat, imagedata, bdat)
elif trimem:
    imagedata = trimarrays.trimzeros(imagedata)
    (bdat, ) = trimarrays.trimto(imagedata, bdat)

imagedata -= bdat
if flatfile is not None:
    imagedata /= fdat

w = wcscoord.wcscoord(ffhdr)

if cutoff > 0.0:
    imagedata = np.clip(imagedata, None, cutoff)

if trimbottom is not None:
    imagedata = imagedata[trimbottom:]
    w.set_offsets(yoffset=trimbottom)
if trimleft is not None:
    imagedata = imagedata[:,trimleft:]
    w.set_offsets(xoffset=trimleft)

if trimright is not None:
    imagedata = imagedata[:,0:-trimright]

plotfigure = plt.figure(figsize=(10,12))
plotfigure.canvas.set_window_title('FITS Image')

med = np.median(imagedata)
mx = imagedata.max()
fi = imagedata.flatten()
fi = fi[fi > med]
pcs = 100.0*(1.0-2.0**-np.arange(pstart,mapsize+pstart-1))
crange = np.concatenate(((0.0,), np.percentile(fi, pcs), (mx,)))
cl=np.log10(np.logspace(1, 256, mapsize)).round()-1
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

odt = 'Unknown date'
for dfld in ('DATE-OBS', 'DATE', '_ATE'):
    if dfld in ffhdr:
        odt = ffhdr[dfld]
        break

tit = ffhdr['OBJECT'] + ' on ' + string.replace(odt, 'T', ' at ') + ' filter ' + ffhdr['FILTER']
plt.title(tit)

ax = plt.gca()
maint = np.loadtxt(mainobjs)
sel = (maint[:,0] >= ramin) & (maint[:,0] <= ramax) & (maint[:,1] >= decmin) & (maint[:,1] <= decmax)
maint = maint[sel]
for m in maint:
    ra = m[0]
    dec = m[1]
    bloc = w.coords_to_pix(((ra, dec),))[0]
    rloc = findnearest.findnearest(imagedata, bloc, mainap, searchrad)
    if rloc is not None:
        newcoords = (rloc[0],rloc[1])
        ptch = mp.Circle(newcoords, radius=mainap, alpha=hilalpha,color=maincolour, fill=False)
        ax.add_patch(ptch)
    ptch = mp.Circle(bloc, radius=mainap, alpha=hilalpha,color=maincolour, fill=True)
    ax.add_patch(ptch)
if figout is None:
    plt.show()
else:
    figout = miscutils.removesuffix(figout, 'png')
    plotfigure.savefig(figout + '.png')
