#! /usr/bin/env python

from astropy.io import fits
from astropy import wcs
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
import numpy as np
import argparse
import sys
import string
import objcoord
import checkcoord
import findobjadu
import warnings

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

parsearg = argparse.ArgumentParser(description='Calculate FTIS ADUs', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('file', type=str, nargs='+', help='FITS files to process')
parsearg.add_argument('--cutoff', type=float, help='Reduce maxima to this value', default=-1.0)
parsearg.add_argument('--trim', action='store_false', help='Trim trailing empty pixels (unless flat file)')
parsearg.add_argument('--coordfile', type=str, required=True, help='Coordingate file to use')
parsearg.add_argument('--apsize', type=int, default=6, help='aperture radius')
parsearg.add_argument('--mainobj', type=str, help='Specify main object if not deduced from FITS file')
parsearg.add_argument('--searchwidth', type=int, default=10, help='Width to search for object either side of coords')
parsearg.add_argument('--flatfile', type=str, help='Flat file to use')
parsearg.add_argument('--biasfile', type=str, help='Bias file to use')

resargs = vars(parsearg.parse_args())
ffnames = resargs['file']
cutoff = resargs['cutoff']
trimem = resargs['trim']
apsize = resargs['apsize']
mainobj = resargs['mainobj']
coordfile = resargs['coordfile']
searchwidth = resargs['searchwidth']
flatfile = resargs['flatfile']
biasfile = resargs['biasfile']

ffrows = False

if flatfile is not None:
    ff = fits.open(flatfile)
    fdat = ff[0].data
    ffrows, ffcols = fdat.shape
    while np.count_nonzero(np.isnan(fdat[-1])) == ffrows:
        fdat = fdat[0:-1]
        ffrows -= 1
    while np.count_nonzero(np.isnan(fdat[:,-1])) == 0:
            fdat = fdat[:,0:-1]
    ffrows, ffcols = fdat.shape

bdat = False
if biasfile is not None:
    bf = fits.open(biasfile)
    bdat = bf[0].data
    if ffrows:
        bdat = bdat[0:ffrows,0:ffcols]
    bdat = bdat + 0.0

coords = np.loadtxt(coordfile)

maincoords = None
if mainobj is not None:
    maincoords = objcoord.obj2coord(mainobj)
    if maincoords is None:
        sys.stdout = sys.stderr
        print "Sorry cannot find coordinates of", mainobj, "in SIMBAD"
        sys.exit(10)
    diffs = np.sum(np.abs(coords - maincoords),axis=1)
    mcc = diffs.argmin()
    refcoords = np.delete(coords, mcc, axis=0)
  
for ffname in ffnames:
    ffile = fits.open(ffname)
    ffhdr = ffile[0].header
    
    dispdate = None
    for dfld in ('DATE-OBS', 'DATE', '_ATE'):
        if dfld in ffhdr:
            dispdate = ffhdr[dfld]
            break
    
    if dispdate is None:
        sys.stdout = sys.stderr
        print "No date found in file", ffname
        sys.stdout = sys.__stdout__
        continue

    imagedata = ffile[0].data

    if ffrows:
        imagedata = imagedata[0:ffrows,0:ffcols]
    elif trimem:
        while np.count_nonzero(imagedata[-1]) == 0:
            imagedata = imagedata[0:-1]

        while np.count_nonzero(imagedata[:,-1]) == 0:
            imagedata = imagedata[:,0:-1]
        
        irows, icols = imagedata.shape
        if bdat:
            bdat = bdat[0:irows,0:icols]

    imagedata = imagedata + 0.0
    if biasfile is not None:
        imagedata = np.clip(imagedata - bdat, 0, None)

    if cutoff > 0.0:
        imagedata = np.clip(imagedata, None, cutoff)
    
    if ffrows:
        imagedata /= fdat
 
    w = wcs.WCS(ffhdr)

    pixrows, pixcols = imagedata.shape
    cornerpix = np.array(((0,0), (pixcols-1, 0), (0, pixrows-1), (pixcols-1, pixrows-1)), np.float)
    cornerradec = w.wcs_pix2world(cornerpix, 0)
    ramax, decmax = cornerradec.max(axis=0)
    ramin, decmin = cornerradec.min(axis=0)
    
    # if we didn't find main object before, find it now. Check that the thing we're looking for is
    # in the area or we're doing something wrong
    
    if maincoords is None:
        mainobj = ffhdr['OBJECT']
        maincoords = objcoord.obj2coord(mainobj)
        if maincoords is None:
            sys.stdout = sys.stderr
            print "Sorry cannot find coordinates of", mainobj, "(specified in file", ffname + ") in SIMBAD"
            sys.stdout = sys.__stdout__
            continue
        diffs = np.sum(np.abs(coords - maincoords),axis=1)
        mcc = diffs.argmin()
        refcoords = np.delete(coords, mcc, axis=0)
    
    if checkcoord.checkcoord(w, imagedata, maincoords, searchwidth, apsize) > 1:
        sys.stdout = sys.stderr
        print "main object", mainobj, "is outside image in file", ffname
        sys.stdout = sys.__stdout__
        continue
    
    errors = 0
    for rf in refcoords:
        if checkcoord.checkcoord(w, imagedata, rf, searchwidth, apsize) > 1:
            sys.stdout = sys.stderr
            print "ref object", rf, "is outside range in file", ffname
            sys.stdout = sys.__stdout__
            errors += 1
    if errors > 0: continue
    
    mainres = findobjadu.findobjadu(w, imagedata, maincoords, searchwidth, apsize)
    if mainres is None:
        sys.stdout = sys.stderr
        print "Did not find", mainobj, "in file", ffname
        sys.stdout = sys.__stdout__
        continue
    
    rfres = []
    
    rc = 1
    for rf in refcoords:
        rfr = findobjadu.findobjadu(w, imagedata, rf, searchwidth, apsize)
        if rfr is None:
            sys.stdout = sys.stderr
            print "Did not find ref obj", rc, " (%.3f %.3f)" % (rf[0],rf[1]), "in file", ffname
            sys.stdout = sys.__stdout__
            errors += 1
        rfres.append(rfr)
        rc += 1
    if errors > 0: continue
 
    rfres = np.array(rfres)
    rfadus = np.sum(rfres[:,2])
    print "%s: %.0f %.0f %#.3g" % (dispdate, mainres[2], rfadus, mainres[2]/rfadus)