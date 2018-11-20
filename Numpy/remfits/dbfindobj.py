#! /usr/bin/env python

# @Author: John M Collins <jmc>
# @Date:   2018-08-25T10:48:07+01:00
# @Email:  jmc@toad.me.uk
# @Filename: imfindobj.py
# @Last modified by:   jmc
# @Last modified time: 2018-11-19T15:45:15+00:00

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
import findnearest
import findbrightest
import calcadus
import remgeom
import dbops
import dbobjinfo
import dbremfitsobj
import math

class duplication(Exception):
    """Throw to get out of duplication loop"""
    pass

parsearg = argparse.ArgumentParser(description='Locate objects in DB FITS files', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('--target', type=str, help='Name of target', required=True)
parsearg.add_argument('--cutoff', type=float, help='Reduce maxima to this value', default=-1.0)
parsearg.add_argument('--trim', action='store_true', help='Trim trailing empty pixels')
parsearg.add_argument('--searchrad', type=int, default=20, help='Search radius in pixels')
parsearg.add_argument('--maxadj', type=float, default=3, help='Max adjustment to RA/DEC in arcmin')
parsearg.add_argument('--mainap', type=int, default=6, help='main aperture radius')
parsearg.add_argument('--nsigfind', default=3.0, type=float, help='Sigmas of ADUs to consider significant')
parsearg.add_argument('--accadjust', action='store_true', help='Accumulate adjustments')
parsearg.add_argument('--targbrightest', action='store_true', help='Take brightest object as target')
parsearg.add_argument('--update', action='store_true', help='Update observations previously found')
parsearg.add_argument('--year', type=int, help='Year to scan (default current year)')
parsearg.add_argument('--month', type=int, help='Month to scan (default current month)')
parsearg.add_argument('--tempdir', type=str, help='Temp directory to unload files default CWD')
parsearg.add_argument('--verbose', action='store_true', help='Give account of actions')

resargs = vars(parsearg.parse_args())
rg = remgeom.load()

# The reason why we don't get RA and DECL info out of this is because we have
# to adjust for proper motion which requires Python 3 (as the versions of astropy that
# support it only run with that)

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)
autils.suppress_vo_warnings()

targetname = resargs['target']
cutoff = resargs['cutoff']
trimem = resargs['trim']
searchrad = resargs['searchrad']
maxadjr = resargs['maxadj']
maxadj = (maxadjr / 60.0) ** 2
mainap = resargs['mainap']
nsigfind = resargs['nsigfind']
targbrightest = resargs['targbrightest']
accadjust = resargs['accadjust']
updateok = resargs['update']
verbose = resargs['verbose']

# Get or validate year and month we're looking at

today = datetime.datetime.now()
year = resargs['year']
month = resargs['month']
if year is None:
    year = today.year
elif year < 2010 or year > today.year:
    print >>sys.stderr, "Invalid year", year
    sys.exit(10)
if month is None:
    month = today.month
elif month > today.month and year == today.year:
    print >>sys.stderr, "Invalid month", month, "for year", year
    sys.exit(11)

tempdir = resargs['tempdir']
if  tempdir is not None:
    try:
        os.chdir(tempdir)
    except OSError as e:
        print >>sys.stderr, "Could not select", tempdir, "error was". e.args[1]
        sys.exit(12)

mydb = dbops.opendb('remfits')
dbcurs = mydb.cursor()

# See if targetname is the object name, otherwise look up as alias

try:
    targetname = dbobjinfo.get_targetname(dbcurs, targetname)
except dbobjinfo.ObjDataError as e:
    print >>sys.stderr, e.args(0)
    sys.exit(100)

flattab, biastab = dbremfitsobj.get_nearest_forbinf(dbcurs, year, month)
nresults = 0

for filter in 'girz':

    print >>sys.stderr, "starting filter", filter

    # First get flat and bias files for month

    ftab = flattab[filter]
    btab = biastab[filter]

    ff = dbremfitsobj.getfits(dbcurs, ftab.fitsind)
    fdat = trimarrays.trimnan(ff[0].data)
    ffrows, ffcols = fdat.shape
    ff.close()

    bf = dbremfitsobj.getfits(dbcurs, btab.fitsind)
    bdat = bf[0].data
    bdat = bdat[0:ffrows,0:ffcols]
    bdat = bdat.astype(np.float64)
    (bdatc, ) = trimarrays.trimto(fdat, bdat)
    bf.close()

    # Note not current flat or bias

    notcurrentflat = ftab.diff != 0 or btab.diff != 0

    # get list of observations for this month

    obslist = dbremfitsobj.get_rem_obs(dbcurs, targetname, year, month, filter)

    if len(obslist) == 0:
        if verbose:
            print >>sys.stderr, "No observations for filter %s for %.2d/%.4d" % (filter, month, year)
        continue

    for obsind, fitsind in obslist:

        previous_obs, previous_nonobs = dbremfitsobj.get_find_results(dbcurs, obsind)
        if  previous_obs + previous_nonobs > 0:
            if updateok:
                dbremfitsobj.del_find_results(dbcurs, obsind, previous_obs > 0, previous_nonobs > 0)
            else:
                if verbose:
                    print >>sys.stderr, "Skipping obsind", obsind, "as done before"
                continue

        ffile = dbremfitsobj.getfits(dbcurs, fitsind)
        ffhdr = ffile[0].header
        imagedata = ffile[0].data.astype(np.float64)
        (imagedata, ) = trimarrays.trimto(fdat, imagedata)
        ffile.close()

        imagedata -= bdatc
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
        cornerpix = ((0,0), (pixcols-1, 0), (0, pixrows-1), (pixcols-1, pixrows-1))
        cornerradec = w.pix_to_coords(cornerpix)
        ramax, decmax = cornerradec.max(axis=0)
        ramin, decmin = cornerradec.min(axis=0)

        # get radius for database search (arcmin) and central coords

        dbsrad = 60.0 * max(decmax-decmin, ramax-ramin)
        racent = (ramax + ramin) / 2.0
        deccent = (decmax + decmin) / 2.0

        odt = None
        for dfld, dfmt in (('MJD-OBS', 'mjd'), ('DATE-OBS', 'isot'), ('DATE' 'isot'), ('_ATE', 'isot')):
            if dfld in ffhdr:
                odt = Time(ffhdr[dfld], format=dfmt)
                break

        if odt is None:
            print >>sys.stderr, "Did not find time in image obsid", obsind
            continue

        # Fetch list of object which might exist from database

        possible_objects = dbobjinfo.get_objlist(dbcurs, racent, deccent, dbsrad, odt)
        print >>sys.stderr, "Possible object search"
        for po in possible_objects:
            radeg, decdeg, objt = po
            print >>sys.stderr, objt.objname, radeg, decdeg

        if len(possible_objects) < 2:
            p = len(possible_objects)
            if p == 0:
                nstr = "No"
                objstr = "objects"
            else:
                nstr = "one"
                objstr = "object"
            dbremfitsobj.add_notfound(dbcurs, obsind, targetname, filter, nstr + " possible " + objstr + " in image", notcurrf = notcurrentflat)
            if verbose:
                print >>sys.stderr, "Skipping", obsind, "as", nstr, "possible", objstr
            continue

        # Prune down that lot to things that can appear in the image

        targobjpl = None
        pruned_objlist = []
        nother = 0

        for possobj in possible_objects:
            adjra, adjdec, objt = possobj
            if adjra < ramin or adjra > ramax: continue
            if adjdec < decmin or adjdec > decmax: continue
            if objt.objname == targetname:
                targobjpl = possobj
                if not targbrightest:
                    pruned_objlist.append(possobj)
            else:
                pruned_objlist.append(possobj)
                nother += 1

        if targobjpl is None:
            dbremfitsobj.add_notfound(dbcurs, obsind, targetname, filter, "Target not in range in image", notcurrf = notcurrentflat)
            if verbose:
                print >>sys.stderr, "Skipping", obsind, "target", targetname, "not available in image"
            continue

        if nother == 0:
            dbremfitsobj.add_notfound(dbcurs, obsind, targetname, filter, "No possible other objects in range for image", notcurrf = notcurrentflat)
            if verbose:
                print >>sys.stderr, "Skipping", obsind, "target", targetname, "only possible object in image"
            continue

        # If we take target as brightest object, then find that first then others

        foundlist = []
        adjras = []
        adjdecs = []

        print >>sys.stderr, "At beginning of search, pruned_objlist length=", len(pruned_objlist)
        if targbrightest:
            print >>sys.stderr, "BRIGHTEST case"
            targra, targdec, tobj = targobjpl
            objpixes = w.coords_to_pix(((targra, targdec),))[0]
            brightest = findbrightest.findbrightest(imagedata, tobj.get_aperture(mainap))
            if  brightest is None:
                dbremfitsobj.add_notfound(dbcurs, obsind, targetname, filter, "Could not find a brightest image", notcurrf = notcurrentflat, apsize = tobj.get_aperture(mainap))
                if verbose:
                    print >>sys.stderr, "Skipping", obsind, "target", targetname, "Could not find brightest image"
                continue
            ncol, nrow, nadu = brightest
            rlpix = ((int(round(ncol)), int(nrow)), )
            rarloc = w.pix_to_coords(rlpix)[0]
            adjra = rarloc[0] - targra
            adjdec = rarloc[1] - targdec
            if adjra**2 + adjdec**2 > maxadj:
                offbr = math.sqrt(adjra**2 + adjdec**2) * 60.0
                offbrs = "Offset of brightest of %.2f exceeds maximum of %.2f" % (offbr, maxadjr)
                dbremfitsobj.add_notfound(dbcurs, obsind, targetname, filter, offbrs, notcurrf = notcurrentflat, apsize = tobj.get_aperture(mainap))
                if verbose:
                    print >>sys.stderr, "Skipping", obsind, "target", targetname, maxbrs
                continue
            adjras.append(adjra)
            adjdecs.append(adjdec)
            foundlist.append((targetname, ncol, nrow, rarloc[0], rarloc[1], tobj.get_aperture(mainap)))

            # Now look for other objects (which don't include target)

            for possible in pruned_objlist:
                objra, objdec, m = possible
                print >>sys.stderr, "Looking for", m.objname
                adjra = objra
                adjdec = objdec
                # If we're tracking adjustments, adjust by average amount so far
                if accadjust:
                    adjra += np.mean(adjras)
                    adjdec += np.mean(adjdecs)
                objpixes = w.coords_to_pix(((adjra, adjdec),))[0]
                nearestobj = findnearest.findnearest(imagedata, objpixes, mainap, searchrad, med + sigma * nsigfind)
                if nearestobj is None:
                    print >>sys.stderr, "Not found"
                    continue
                ncol, nrow, nadu = nearestobj
                rlpix = ((int(round(ncol)), int(nrow)), )
                rarloc = w.pix_to_coords(rlpix)[0]
                adjra = rarloc[0] - objra
                adjdec = rarloc[1] - objdec
                if adjra**2 + adjdec**2 > maxadj:
                    print >>sys.stderr, "Too far away"
                    continue
                adjras.append(rarloc[0] - objra)
                adjdecs.append(rarloc[1] - objdec)
                foundlist.append((m.objname, ncol, nrow, rarloc[0], rarloc[1], mainap))
                print >>sys.stderr, "Found it"
        else:
            print >>sys.stderr, "Non brightest case"
            for possible in pruned_objlist:
                objra, objdec, m = possible
                print >>sys.stderr, "FN Looking for", m.objname
                adjra = objra
                adjdec = objdec
                # If we're tracking adjustments, adjust by average amount so far
                if accadjust and len(adjras) != 0:
                    adjjra += np.mean(adjras)
                    adjdec += np.mean(adjdecs)
                objpixes = w.coords_to_pix(((adjra, adjdec),))[0]
                nearestobj = findnearest.findnearest(imagedata, objpixes, mainap, searchrad, med + sigma * nsigfind)
                if nearestobj is None:
                    continue
                if m.objname == targetname:
                    targobjpl = possible
                ncol, nrow, nadu = nearestobj
                rlpix = ((int(round(ncol)), int(nrow)), )
                rarloc = w.pix_to_coords(rlpix)[0]
                adjra = rarloc[0] - objra
                adjdec = rarloc[1] - objdec
                if adjra**2 + adjdec**2 > maxadj:
                    continue
                adjras.append(rarloc[0] - objra)
                adjdecs.append(rarloc[1] - objdec)
                foundlist.append((m.objname, ncol, nrow, rarloc[0], rarloc[1], mainap))

        print >>sys.stderr, "RA adjs", adjras, "DEC adjs", adjdecs
        if targobjpl is None:
            dbremfitsobj.add_notfound(dbcurs, obsind, targetname, filter, "Failed to find targer", notcurrf = notcurrentflat, apsize = mainap, searchrad = searchrad)
            if verbose:
                print >>sys.stderr, "Skipping", obsind, "target", targetname, "not found in image"
            continue

        if len(foundlist) < 2:
            dbremfitsobj.add_notfound(dbcurs, obsind, targetname, filter, "No reference objects found", notcurrf = notcurrentflat, apsize = mainap, searchrad = searchrad)
            if verbose:
                print >>sys.stderr, "Skipping", obsind, "target", targetname, "No reference objects found"
            continue

        for result in foundlist:
            objname, ncol, nrow, radeg, decdeg, apsize = result
            ncol, nrow = w.abspix((ncol, nrow))
            dbremfitsobj.add_objident(dbcurs, obsind, targetname, objname, filter, ncol, nrow, radeg, decdeg, apsize, searchrad, notcurrf = notcurrentflat)
            nresults += 1

if verbose:
    print >>sys.stderr, nresults, "results added"

sys.exit(0)
