#! /usr/bin/env python

from astropy.io import fits
from astropy import wcs
import matplotlib.pyplot as plt
import matplotlib.patches as mp
from matplotlib import colors 
import numpy as np
import argparse
import sys
import string

parsearg = argparse.ArgumentParser(description='Plot FITS image', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('file', type=str, nargs=1, help='FITS file to plot can be compressed')
parsearg.add_argument('--cutoff', type=float, help='Reduce maxima to this value', default=-1.0)
parsearg.add_argument('--trim', action='store_true', help='Trim trailing empty pixels')
parsearg.add_argument('--mapsize', type=int, default=24, help='Number of shades in grey scale')
parsearg.add_argument('--divisions', type=int, default=4, help='Divisions in RA/Dec lines')
parsearg.add_argument('--divprec', type=int, default=3, help='Precision for axes')
parsearg.add_argument('--pstart', type=int, default=4, help='2**-n fraction to start display at')
parsearg.add_argument('--divthresh', type=int, default=5, help='Pixels from edge for displaying divisions')
parsearg.add_argument('--racolour', type=str, default='#FFCCCC', help='Colour of RA lines')
parsearg.add_argument('--deccolour', type=str, default='#CCCCFF', help='Colour of DEC lines')
parsearg.add_argument('--apsize', type=int, default=6, help='aperture radius')
parsearg.add_argument('--blanksize', type=int, default=20, help='Size to blank')
parsearg.add_argument('--numobj', type=int, default=3, help='Number of brightests objects to display')
parsearg.add_argument('--hilcolour', type=str, default='r', help='Object colour')
parsearg.add_argument('--hilalpha', type=float, default=0.75, help='Object alpha')                  

resargs = vars(parsearg.parse_args())
ffname = resargs['file'][0]

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

apsize = resargs['apsize']
blanksize = resargs['blanksize']
numobj = resargs['numobj']
hilcolour = resargs['hilcolour']
hilalpha = resargs['hilalpha']

imagedata = ffile[0].data

if trimem:
    while np.count_nonzero(imagedata[-1]) == 0:
        imagedata = imagedata[0:-1]

    while np.count_nonzero(imagedata[:,-1]) == 0:
        imagedata = imagedata[:,0:-1]

imagedata = imagedata + 0.0

if cutoff > 0.0:
    imagedata = np.clip(imagedata, None, cutoff)

plt.figure(figsize=(10,12))

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
devnull = open('/dev/null', 'w')

sys.stderr = devnull
w = wcs.WCS(ffhdr)
sys.stderr = sys.__stderr__

cornerpix = np.array(((0,0), (0, pixcols-1), (pixrows-1, 0), (pixrows-1, pixcols-1)), np.float)

cornerradec = w.wcs_pix2world(cornerpix, 1)

# Get matrix of ra/dec each pixel

pixarray = np.array([[(x,y) for x in range(0,pixcols)] for y in range(0,pixrows)])
pixcoords = w.wcs_pix2world(pixarray.reshape(pixrows*pixcols,2), 1).reshape(pixrows,pixcols,2)
ratable = pixcoords[:,:,0]
dectable = pixcoords[:,:,1]
ramax, decmax = cornerradec.max(axis=0)
ramin, decmin = cornerradec.min(axis=0)

radivs = np.linspace(ramin, ramax, divisions).round(divprec)
decdivs = np.linspace(decmin, decmax, divisions).round(divprec)

ratpos = []
dectpos = []
raused = []
decused = []

for r in radivs:
    ra_y = np.arange(0, pixrows)
    diffs = np.abs(ratable-r)
    ra_x = diffs.argmin(axis=1)
    sel = (ra_x > 0) & (ra_x < pixcols-1)
    ra_x = ra_x[sel]
    ra_y = ra_y[sel]
    if len(ra_x) == 0: continue
    if ra_y.min() < divthresh:
        ratpos.append(ra_x[ra_y.argmin()])
        raused.append(r)
    plt.plot(ra_x, ra_y, color=racol, alpha=0.5)

for d in decdivs:
    dec_x = np.arange(0, pixcols)
    diffs = np.abs(dectable-d)
    dec_y = diffs.argmin(axis=0)
    sel = (dec_y > 0) & (dec_y < pixrows-1)
    dec_x = dec_x[sel]
    dec_y = dec_y[sel]
    if len(dec_x) == 0: continue
    if dec_x.min() < divthresh:
        dectpos.append(dec_y[dec_x.argmin()])
        decused.append(d)
    plt.plot(dec_x, dec_y, color=deccol, alpha=0.5)

ratpos = np.array(ratpos)
dectpos = np.array(dectpos)
raused = np.array(raused)
decused = np.array(decused)

sel = (ratpos > 0) & (ratpos < pixcols-1)
ratpos = ratpos[sel]
raused = raused[sel]
sel = (dectpos > 0) & (dectpos < pixrows-1)
dectpos = dectpos[sel]
decused = decused[sel]
fmt = '%.' + str(divprec) + 'f'
rafmt = [fmt % r for r in raused]
decfmt = [fmt % d for d in decused]
plt.xticks(ratpos, rafmt)
plt.yticks(dectpos, decfmt)
plt.xlabel('RA (deg)')
plt.ylabel('Dec (deg)')

ax = plt.gca()
for nb in range(0,numobj):
    brows, bcols = np.where(imagedata==imagedata.max())
    brow = brows[0]
    bcol = bcols[0]
    ptch = mp.Circle((bcol,brow), radius=apsize, alpha=hilalpha,color=hilcolour)
    ax.add_patch(ptch)
    imagedata[max(0,brow-blanksize):min(pixrows-1,brow+blanksize),max(0,bcol-blanksize):min(pixcols-1,bcol+blanksize)] = med

plt.title(ffhdr['OBJECT'] + ' on ' + string.replace(ffhdr['DATE'], 'T', ' at ') + ' filter ' + ffhdr['FILTER'])
plt.show()
