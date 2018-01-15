#! /usr/bin/env python

from astropy.io import fits
from astropy import wcs
import numpy as np
import argparse
import sys
import string
import objcoord
import checkcoord
import findobjadu

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
refobjs = resargs['refobjs']
searchwidth = resargs['searchwidth']

maincoords = None
if mainobj is not None:
    maincoords = objcoord.obj2coord(mainobj)
    if maincoords is None:
        sys.stdout = sys.stderr
        print "Sorry cannot find coordinates of", mainobj, "in SIMBAD"
        sys.exit(10)

refcoords = []
errors = 0
for rf in refobjs:
    rc = objcoord.obj2coord(rf)
    if rc is None:
        sys.stdout = sys.stderr
        print "Sorry cannot find coordinates of ref object", rf, "in SIMBAD"
        errors += 1
    refcoords.append(rc)

if errors != 0:
    sys.exit(11)
    
devnull = open('/dev/null', 'w')

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
 
    sys.stderr = devnull
    w = wcs.WCS(ffhdr)
    sys.stderr = sys.__stderr__

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
    
    if checkcoord.checkcoord(w, imagedata, maincoords, searchwidth, apsize) != 0:
        sys.stdout = sys.stderr
        print "main object", mainobj, "is outside image in file", ffname
        sys.stdout = sys.__stdout__
        continue
    
    errors = 0
    for rf,rfname in zip(refcoords, refobjs):
        if checkcoord.checkcoord(w, imagedata, rf, searchwidth, apsize) != 0:
            sys.stdout = sys.stderr
            print "ref object", rfname, "is outside range in file", ffname
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
    
    for rf,rfname in zip(refcoords, refobjs):
        rfr = findobjadu.findobjadu(w, imagedata, rf, searchwidth, apsize)
        if rfr is None:
            sys.stdout = sys.stderr
            print "Did not find", rfname, "ib file", ffname
            sys.stdout = sys.__stdout__
            errors += 1
        rfres.append(rfr)
    if errors > 0: continue
 
    rfres = np.array(rfres)
    rfadus = np.sum(rfres[:,2])
    print "%s: %.0f %.0f %.3f" % (ffhdr["_ATE"], mainres[2], rfadus, mainres[2]/rfadus)