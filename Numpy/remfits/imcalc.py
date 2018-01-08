#! /usr/bin/env python

from astropy.io import fits
from astropy import wcs
import numpy as np
import argparse
import sys
import string

parsearg = argparse.ArgumentParser(description='Calculate FTIS ADUs', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('file', type=str, nargs='+', help='FITS files to process')
parsearg.add_argument('--cutoff', type=float, help='Reduce maxima to this value', default=-1.0)
parsearg.add_argument('--trim', action='store_true', help='Trim trailing empty pixels')
parsearg.add_argument('--apsize', type=int, default=6, help='aperture radius')
parsearg.add_argument('--mainobj', type=str, help='Specify main object if not deduced from FITS file')
parsearg.add_argument('--refobjs', type=str, nargs='+', help='Specify reference objects', required=True)
parsearg.add_argument('--searchwidth', type=int, default=20, help='Width to search for object either side of coords')

resargs = vars(parsearg.parse_args())
ffnames = resargs['file']
cutoff = resargs['cutoff']
trimem = resargs['trim']
apsize = resargs['apsize']
mainobj = resargs['mainobj']
refobjs = resargs['refobj']
searchwidth = resargs['searchwidth']

for ffname in ffnames:
    ffile = fits.open(ffname)
    ffhdr = ffile[0].header

    imagedata = ffile[0].data

    if trimem:
        while np.count_nonzero(imagedata[-1]) == 0:
            imagedata = imagedata[0:-1]

        while np.count_nonzero(imagedata[:,-1]) == 0:
            imagedata = imagedata[:,0:-1]

    imagedata = imagedata + 0.0

    if cutoff > 0.0:
        imagedata = np.clip(imagedata, None, cutoff)

    med = np.median(imagedata)
    mx = imagedata.max()

    pixrows, pixcols = imagedata.shape
    
    imagedate = np.clip(imagedata - med, 0.0, None)
    
    adus = [ med ]
    
    for nb in range(0,numobj):
        brows, bcols = np.where(imagedata==imagedata.max())
        brow = brows[0]
        bcol = bcols[0]
        rads = np.sqrt(np.add.outer((np.arange(0,pixrows)-brow)**2,(np.arange(0,pixcols)-bcol)**2))
        inrad = rads <= apsize
        outrad = rads > apsize
        rads[inrad] = 1.0
        rads[outrad] = 0.0
        adus.append(np.sum(imagedate*rads))
        imagedata[max(0,brow-blanksize):min(pixrows-1,brow+blanksize),max(0,bcol-blanksize):min(pixcols-1,bcol+blanksize)] = 0.0
    #print ffname, adus
    fmt = ffname + "\t%.1f\t" + string.join(["%d"] * numobj, "\t")
    print fmt % tuple(adus)
     
