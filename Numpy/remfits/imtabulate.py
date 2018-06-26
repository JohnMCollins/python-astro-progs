#! /usr/bin/env python

from astropy.io import fits
from astropy import wcs
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
from astropy.time import Time
import astroquery.utils as autils
import numpy as np
import argparse
import sys
import datetime
import os.path
import string
import objcoord
import trimarrays
import wcscoord
import warnings
import miscutils
import objinfo
import findnearest
import findbrightest

class duplication(Exception):
    """Throw to get out of duplication loop"""
    pass

parsearg = argparse.ArgumentParser(description='Tabulate ADUs from FITS files', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', type=str, nargs='+', help='FITS file to plot can be compressed')
parsearg.add_argument('--libfile', type=str, default='~/lib/stellar_data', help='File to use for database')
parsearg.add_argument('--cutoff', type=float, help='Reduce maxima to this value', default=-1.0)
parsearg.add_argument('--trim', action='store_true', help='Trim trailing empty pixels')
parsearg.add_argument('--flatfile', type=str, help='Flat file to use')
parsearg.add_argument('--biasfile', type=str, help='Bias file to use')
parsearg.add_argument('--trimbottom', type=int, help='Pixels to trim off bottom of picture')
parsearg.add_argument('--trimleft', type=int, help='Pixels to trim off left of picture')
parsearg.add_argument('--trimright', type=int, help='Pixels to trim off right of picture')
parsearg.add_argument('--searchrad', type=int, default=20, help='Search radius in pixels')
parsearg.add_argument('--target', type=str, help='Name of target')
parsearg.add_argument('--mainap', type=int, default=6, help='main aperture radius')
parsearg.add_argument('--nsigfind', default=3.0, type=float, help='Sigmas of ADUs to consider significant')
parsearg.add_argument('--accadjust', action='store_true', help='Accumulate adjustments')
parsearg.add_argument('--targbrightest', action='store_true', help='Take brightest object as target')
parsearg.add_argument('--skylevel', type=float, help='Value to subtract for sky level otherwise use median')

resargs = vars(parsearg.parse_args())
ffnames = resargs['files']

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

cutoff = resargs['cutoff']
trimem = resargs['trim']

flatfile = resargs['flatfile']
biasfile = resargs['biasfile']

trimbottom = resargs['trimbottom']
trimleft = resargs['trimleft']
trimright = resargs['trimright']

nsigfind = resargs['nsigfind']

searchrad = resargs['searchrad']
target = resargs['target']
if target is not None:
    try:
        target = objinf.get_main(target)
    except objinfo.ObjInfoError as e:
        print >>sys.stderr, e.args[0]
        sys.exit(30)
mainap = resargs['mainap']
targbrightest = resargs['targbrightest']
accadjust = targbrightest or resargs['accadjust']
skylevel = resargs['skylevel']

if flatfile is not None:
    ff = fits.open(flatfile)
    fdat = trimarrays.trimnan(ff[0].data)
    ffrows, ffcols = fdat.shape

if biasfile is not None:
    bf = fits.open(biasfile)
    bdat = bf[0].data
    if flatfile is not None:
        bdat = bdat[0:ffrows,0:ffcols]
    bdat = bdat.astype(np.float64)

#else:
#    bdat = np.zeros_like(imagedata)

for ffname in ffnames:
    ffile = fits.open(ffname)
    ffhdr = ffile[0].header

    imagedata = ffile[0].data.astype(np.float64)
    
    if biasfile is None:
        bdat = np.zeros_like(imagedata)

    if flatfile is not None:
        imagedata, bdatc = trimarrays.trimto(fdat, imagedata, bdat)
    elif trimem:
        imagedata = trimarrays.trimzeros(imagedata)
        (bdatc, ) = trimarrays.trimto(imagedata, bdat)

    imagedata -= bdatc
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

    if skylevel is None:
        med = np.median(imagedata)
    else:
        med = skylevel
    sigma = imagedata.std()
    imagedata = np.clip(imagedata-med, 0, None)
    mx = imagedata.max()

    # OK get coords of edges of picture

    pixrows, pixcols = imagedata.shape
    cornerpix = ((0,0), (pixcols-1, 0), (9, pixrows-1), (pixcols-1, pixrows-1))
    cornerradec = w.pix_to_coords(cornerpix)
    ramax, decmax = cornerradec.max(axis=0)
    ramin, decmin = cornerradec.min(axis=0)

    odt = datetime.datetime.now()
    for dfld in ('DATE-OBS', 'DATE', '_ATE'):
        if dfld in ffhdr:
            odt = ffhdr[dfld]
            break

    # Reduce pruned list to objusts that could be in image

    targobj = None
    pruned_objlist = []
    for objl in objinf.list_objects(odt):
        obj, ra, dec = objl
        if ra < ramin or ra > ramax: continue
        if dec < decmin or dec > decmax: continue
        if obj.objname == target:
            targobj = objl
            if not targbrightest:
                pruned_objlist.append(targobj)
        else:
            pruned_objlist.append(objl)

    # Look for objects but eliminate duplicate finds

	odt = Time(odt).datetime
    nodup_objlist = []
    radsq = mainap**2
    adjras = []
    adjdecs = []
    Hadtarg = None

    if targbrightest:
        if targobj is None:
            print >>sys.stderr, "Did not find target", target, "within image coords"
            continue
        tobj, targra, targdec = targobj
        objpixes = w.coords_to_pix(((targra, targdec),))[0]
        brightest = findbrightest.findbrightest(imagedata, mainap)
        if brightest is None:
            print >>sys.stderr, "Could not find a brightest object"
            continue
        ncol, nrow, nadu = brightest
        rlpix = ((int(round(ncol)), int(nrow)), )
        rarloc = w.pix_to_coords(rlpix)[0]
        nodup_objlist.append((ncol, nrow, nadu, objpixes, targra, targdec, rarloc, tobj))
        Hadtarg = nodup_objlist[-1]
        adjras.append(rarloc[0]-targra)
        adjdecs.append(rarloc[1]-targdec)
    
    for mtch in pruned_objlist:
        m, objra, objdec = mtch
        adjra = objra
        adjdec = objdec
        if accadjust and len(adjras) != 0:
            adjra += np.mean(adjras)
            adjdec += np.mean(adjdecs)
        objpixes = w.coords_to_pix(((adjra, adjdec),))[0]
        nearestobj = findnearest.findnearest(imagedata, objpixes, mainap, searchrad, med + sigma * nsigfind)
        if nearestobj is None:
            continue
        ncol, nrow, nadu = nearestobj
        try:
            for m2 in nodup_objlist:
                if (m2[0] - ncol) ** 2 + (m2[1] - nrow) ** 2 < radsq:
                    raise duplication("dup")
            rlpix = ((int(round(ncol)), int(nrow)), )
            rarloc = w.pix_to_coords(rlpix)[0]
            nodup_objlist.append((ncol, nrow, nadu, objpixes, objra, objdec, rarloc, m))
            if m.objname == target: Hadtarg = nodup_objlist[-1]
            adjras.append(rarloc[0]-objra)
            adjdecs.append(rarloc[1]-objdec)
        except duplication:
            pass
     
    if Hadtarg is None:
        continue
    ept = odt.strftime("%Y-%m-%d %H-%M-%S:")
    print ept, "sky level:", "%.4g" % med
    targadu = Hadtarg[2]
    for mtch in nodup_objlist:
        ncol, nrow, nadu, objpixes, objra, objdec,rarloc, m = mtch
        if m.objname != target:
			print "%s %s %.6g %.6g" % (ept, m.objname, nadu, targadu / nadu)
        else:
			print "%s %s: %.6g" % (ept, m.objname, nadu)

