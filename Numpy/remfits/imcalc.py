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
parsearg.add_argument('--trim', action='store_true', help='Trim trailing empty pixels')
parsearg.add_argument('--coordfile', type=str, required=True, help='Coordingate file to use')
parsearg.add_argument('--apsize', type=int, default=6, help='aperture radius')
parsearg.add_argument('--mainobj', type=str, help='Specify main object if not deduced from FITS file')
parsearg.add_argument('--searchwidth', type=int, default=10, help='Width to search for object either side of coords')

resargs = vars(parsearg.parse_args())
ffnames = resargs['file']
cutoff = resargs['cutoff']
trimem = resargs['trim']
apsize = resargs['apsize']
mainobj = resargs['mainobj']
coordfile = resargs['coordfile']
searchwidth = resargs['searchwidth']

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

    imagedata = ffile[0].data

    if trimem:
        while np.count_nonzero(imagedata[-1]) == 0:
            imagedata = imagedata[0:-1]

        while np.count_nonzero(imagedata[:,-1]) == 0:
            imagedata = imagedata[:,0:-1]

    imagedata = imagedata + 0.0

    if cutoff > 0.0:
        imagedata = np.clip(imagedata, None, cutoff)
 
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
            print "ref object is outside range in file", ffname
            sys.stdout = sys.__stdout__
            errors += 1
    if errors > 0: continue
    
    mainres = findobjadu.findobjadu(w, imagedata, maincoords, searchwidth, apsize)
    if mainres is None:
        sys.stdout = sys.stderr
        print "Did not find", mainobj, "in file2, ffname"
        sys.stdout = sys.__stdout__
        continue
    
    rfres = []
    
    rc = 1
    for rf in refcoords:
        rfr = findobjadu.findobjadu(w, imagedata, rf, searchwidth, apsize)
        if rfr is None:
            sys.stdout = sys.stderr
            print "Did not find ref obj", rc, "in file", ffname
            sys.stdout = sys.__stdout__
            errors += 1
        rfres.append(rfr)
        rc += 1
    if errors > 0: continue
 
    rfres = np.array(rfres)
    rfadus = np.sum(rfres[:,2])
    print "%s: %.0f %.0f %.3g" % (ffhdr["_ATE"], mainres[2], rfadus, mainres[2]/rfadus)