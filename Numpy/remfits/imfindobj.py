#! /usr/bin/env python

# @Author: John M Collins <jmc>
# @Date:   2018-08-25T10:48:07+01:00
# @Email:  jmc@toad.me.uk
# @Filename: imfindobj.py
# @Last modified by:   jmc
# @Last modified time: 2018-10-01T17:47:46+01:00

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
import calcadus
import remgeom
import remfitsobj

class duplication(Exception):
    """Throw to get out of duplication loop"""
    pass

parsearg = argparse.ArgumentParser(description='Locate objects in FITS files', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', type=str, nargs='+', help='FITS files to scan')
parsearg.add_argument('--results', type=str, required=True, help='Results XML file')
parsearg.add_argument('--libfile', type=str, default='~/lib/stellar_data', help='File to use for database')
parsearg.add_argument('--cutoff', type=float, help='Reduce maxima to this value', default=-1.0)
parsearg.add_argument('--trim', action='store_true', help='Trim trailing empty pixels')
parsearg.add_argument('--flatfile', type=str, help='Flat file to use')
parsearg.add_argument('--biasfile', type=str, help='Bias file to use')
parsearg.add_argument('--searchrad', type=int, default=20, help='Search radius in pixels')
parsearg.add_argument('--maxadj', type=float, default=3, help='Max adjustment to RA/DEC in arcmin')
parsearg.add_argument('--target', type=str, help='Name of target')
parsearg.add_argument('--mainap', type=int, default=6, help='main aperture radius')
parsearg.add_argument('--nsigfind', default=3.0, type=float, help='Sigmas of ADUs to consider significant')
parsearg.add_argument('--accadjust', action='store_true', help='Accumulate adjustments')
parsearg.add_argument('--targbrightest', action='store_true', help='Take brightest object as target')
parsearg.add_argument('--update', action='store_true', help='Update observations previously found')
parsearg.add_argument('--basedir', type=str, help='Set directory as base directory in file')

resargs = vars(parsearg.parse_args())
ffnames = resargs['files']

libfile = os.path.expanduser(resargs['libfile'])

rg = remgeom.load()

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

resultsfile = resargs['results']

cutoff = resargs['cutoff']
trimem = resargs['trim']

flatfile = resargs['flatfile']
biasfile = resargs['biasfile']

nsigfind = resargs['nsigfind']

searchrad = resargs['searchrad']
maxadj = (resargs['maxadj'] / 60.0) ** 2
targetname = resargs['target']
if targetname is not None:
    try:
        target = objinf.get_main(targetname)
    except objinfo.ObjInfoError as e:
        print >>sys.stderr, e.args[0]
        sys.exit(30)

rfinf = remfitsobj.RemobjSet(target)
cwd = rfinf.basedir
try:
    rfinf.loadfile(resultsfile)
    if rfinf.basedir != cwd:
        rfinf.set_basedir(cwd)
    if rfinf.targname is not None and rfinf.targname != target:
        print >>Sys.stderr, "target for", targetname, "does not match that in file of", rfinf.targname
        sys.exit(20)
except remfitsobj.RemObjError as e:
    if e.warningonly:
        print  >>sys.stderr, "(Warning) creating new:", resultsfile
    else:
        print >>sys.stderr,  "Error loading file", e.args[0]
        sys.exit(21)

mainap = resargs['mainap']
targbrightest = resargs['targbrightest']
accadjust = targbrightest or resargs['accadjust']
updateok = resargs['update']

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

    imagedata -= bdat
    if flatfile is not None:
        imagedata /= fdat

    w = wcscoord.wcscoord(ffhdr)

    if cutoff > 0.0:
        imagedata = np.clip(imagedata, None, cutoff)

    if rg.trims.bottom is not None:
        imagedata = imagedata[rg.trims.bottom:]
        w.set_offsets(yoffset=rg.trims.bottom)

    if rg.trims.left is not None:
        imagedata = imagedata[:,rg.trims.left:]
        w.set_offsets(xoffset=rg.trims.left)

    if rg.trims.right is not None:
        imagedata = imagedata[:,0:-rg.trims.right]

    med = np.median(imagedata)
    sigma = imagedata.std()

    # OK get coords of edges of picture

    pixrows, pixcols = imagedata.shape
    cornerpix = ((0,0), (pixcols-1, 0), (9, pixrows-1), (pixcols-1, pixrows-1))
    cornerradec = w.pix_to_coords(cornerpix)
    ramax, decmax = cornerradec.max(axis=0)
    ramin, decmin = cornerradec.min(axis=0)

    odt = None
    for dfld, dfmt in (('MJD-OBS', 'mjd'), ('DATE-OBS', 'isot'), ('DATE' 'isot'), ('_ATE', 'isot')):
        if dfld in ffhdr:
            odt = Time(ffhdr[dfld], format=dfmt)
            break

    if odt is None:
        print >>sys.stderr, "Did not find time in file", ffname
        continue

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

	nodup_objlist = []
    radsq = mainap**2
    adjras = []
    adjdecs = []
    Hadtarg = None

    if targbrightest:
        if targobj is None:
            print >>sys.stderr, "Did not find target", target, "within image coords in file", ffname
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
        adjra = rarloc[0]-targra
        adjdec = rarloc[1]-targdec
        if adjra**2 + adjdec**2 > maxadj:
            print >>sys.stderr, "Offset of brighest object too big in file", ffname
            continue
        nodup_objlist.append((ncol, nrow, nadu, objpixes, targra, targdec, rarloc, tobj))
        Hadtarg = nodup_objlist[-1]
        adjras.append(adjra)
        adjdecs.append(adjdec)

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
        print >>sys.stderr, "Algorithm did not find target", target, "within image coords in file", ffname
        continue

    newobjlist = remfitsobj.Remobjlist(ffname, odt.mjd, ffhdr['FILTER'])
    for mtch in nodup_objlist:
        ncol, nrow, nadu, objpixes, objra, objdec, rarloc, m = mtch
        absc, absr = w.abspix((ncol,nrow))
        objdets = remfitsobj.Remobj(m.objname, absc, absr, rarloc[0], rarloc[1])
        if m.objname == target:
            newobjlist.addtarget(objdets)
        else:
            newobjlist.addobj(objdets)

    newobjlist.airmass = ffhdr['AIRMASS']
    rfinf.addobs(newobjlist, updateok)

if resargs['basedir'] is not None:
    rfinf.set_basedir(resargs['basedir'])
rfinf.savefile(resultsfile)
