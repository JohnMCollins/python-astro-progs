#! /usr/bin/env python

from astropy.io import fits
import matplotlib.pyplot as plt
from matplotlib import colors 
import numpy as np
import argparse

parsearg = argparse.ArgumentParser(description='Plot FITS image', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('file', type=str, nargs=1, help='FITS file to plot can be compressed')
parsearg.add_argument('--cutoff', type=float, help='Reduce maxima to this value', default=-1.0)
parsearg.add_argument('--trim', action='store_true', help='Trim trailing empty pixels')
parsearg.add_argument('--power', type=float, help='Set power law normalisation')
parsearg.add_argument('--lbound', type=float, default=0.0, help='Lower bound for colour map')
parsearg.add_argument('--ubound', type=float, help='Upper bound for colour map')
parsearg.add_argument('--mapsize', type=int, default=24, help='Number of shades in grey scale')

resargs = vars(parsearg.parse_args())
ffname = resargs['file'][0]

ffile = fits.open(ffname)
cutoff = resargs['cutoff']
trimem = resargs['trim']
pwr = resargs['power']
lbound = resargs['lbound']
ubound = resargs['ubound']
mapsize = resargs['mapsize']

imagedata = ffile[0].data

if trimem:
    while np.count_nonzero(imagedata[-1]) == 0:
        imagedata = imagedata[0:-1]

    while np.count_nonzero(imagedata[:,-1]) == 0:
        imagedata = imagedata[:,0:-1]

imagedata = imagedata + 0.0

if cutoff > 0.0:
    imagedata[imagedata > cutoff] = cutoff

if ubound is not None:
    mx = imagedata.max()
    if ubound > mx:
        ubound = mx
    ngen = mapsize
    pref = []
    suff = []
    top = ubound
    if top < mx:
        top = mx
        ngen -= 1
        suff.append(mx)
    if lbound > 0.0:
        pref.append(0.0)
        ngen -= 1
    crange = np.concatenate((pref, np.linspace(lbound, ubound, ngen),suff))
    cl=np.log10(np.logspace(1, 256, mapsize)).round()-1
    collist = ["#%.2x%.2x%.2x" % (i,i,i) for i in cl]
    cmap = colors.ListedColormap(collist)
    norm = colors.BoundaryNorm(crange, cmap.N)
    img = plt.imshow(imagedata, cmap=cmap, norm=norm, origin='lower')
    plt.colorbar(img, norm=norm, cmap=cmap, boundaries=crange, ticks=crange)
elif pwr is not None:
    img = plt.imshow(imagedata, cmap='gray', origin='lower', norm=colors.PowerNorm(pwr))
    plt.colorbar(img)
else:
    img = plt.imshow(imagedata, cmap='gray', origin='lower')
    plt.colorbar(img)
plt.show()
