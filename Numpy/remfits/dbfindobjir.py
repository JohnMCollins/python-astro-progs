#! /usr/bin/env python3

# @Author: John M Collins <jmc>
# @Date:   2018-08-25T10:48:07+01:00
# @Email:  jmc@toad.me.uk
# @Filename: imfindobj.py
# @Last modified by:   jmc
# @Last modified time: 2019-01-04T22:57:49+00:00

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

class FoundData(object):
    """Record a putative found object"""

    def __init__(self, dist, name, col, row, ra, dec, raadj, decadj, apsize):
        self.dist = dist
        self.name = name
        self.col = col
        self.row = row
        self.ra = ra
        self.dec = dec
        self.raadj = raadj
        self.decadj = decadj
        self.apsize = apsize

    def __hash__(self):
        return  self.col * 100000 + self.row

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
    print("Invalid year", year, file=sys.stderr)
    sys.exit(10)
if month is None:
    month = today.month
elif month > today.month and year == today.year:
    print("Invalid month", month, "for year", year, file=sys.stderr)
    sys.exit(11)

tempdir = resargs['tempdir']
if  tempdir is not None:
    try:
        os.chdir(tempdir)
    except OSError as e:
        print("Could not select", tempdir, "error was". e.args[1], file=sys.stderr)
        sys.exit(12)

mydb = dbops.opendb('remfits')
dbcurs = mydb.cursor()

# See if targetname is the object name, otherwise look up as alias

try:
    targetname = dbobjinfo.get_targetname(dbcurs, targetname)
except dbobjinfo.ObjDataError as e:
    print(e.args(0), file=sys.stderr)
    sys.exit(100)

flattab, biastab = dbremfitsobj.get_nearest_forbinf(dbcurs, year, month)
nresults = 0

for filter in 'HJK':

    # get list of observations for this month

    obslist = dbremfitsobj.get_rem_obs(dbcurs, targetname, year, month, filter)

    if len(obslist) == 0:
        if verbose:
            print("No observations for filter %s for %.2d/%.4d" % (filter, month, year), file=sys.stderr)
        continue

    for obsind, fitsind, exptime in obslist:

        previous_obs, previous_nonobs = dbremfitsobj.get_find_results(dbcurs, obsind)
        if  previous_obs + previous_nonobs > 0:
            if updateok:
                dbremfitsobj.del_find_results(dbcurs, obsind, previous_obs > 0, previous_nonobs > 0)
            else:
                if verbose:
                    print("Skipping obsind", obsind, "as done before", file=sys.stderr)
                continue

        ffile = dbremfitsobj.getfits(dbcurs, fitsind)
        ffhdr = ffile[0].header
        imagedata = ffile[0].data.astype(np.float64)
        ffile.close()

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
            print("Did not find time in image obsid", obsind, file=sys.stderr)
            continue

        # Fetch list of object which might exist from database

        possible_objects = dbobjinfo.get_objlist(dbcurs, racent, deccent, dbsrad, odt)
        if len(possible_objects) < 2:
            p = len(possible_objects)
            if p == 0:
                nstr = "No"
                objstr = "objects"
            else:
                nstr = "one"
                objstr = "object"
            dbremfitsobj.add_notfound(dbcurs, obsind, targetname, filter, exptime, nstr + " possible " + objstr + " in image", notcurrf = notcurrentflat)
            if verbose:
                print("Skipping", obsind, "as", nstr, "possible", objstr, file=sys.stderr)
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
            dbremfitsobj.add_notfound(dbcurs, obsind, targetname, filter, exptime, "Target not in range in image", notcurrf = notcurrentflat)
            if verbose:
                print("Skipping", obsind, "target", targetname, "not available in image", file=sys.stderr)
            continue

        # If we take target as brightest object, then find that first then others

        clookup = dict()

        if targbrightest:
            targra, targdec, tobj = targobjpl
            objpixes = w.coords_to_pix(((targra, targdec),))[0]
            brightest = findbrightest.findbrightest(imagedata, tobj.get_aperture(mainap))
            if  brightest is None:
                dbremfitsobj.add_notfound(dbcurs, obsind, targetname, filter, "Could not find a brightest image", notcurrf = notcurrentflat, apsize = tobj.get_aperture(mainap))
                if verbose:
                    print("Skipping", obsind, "target", targetname, "Could not find brightest image", file=sys.stderr)
                continue
            ncol, nrow, nadu = brightest
            ncol = int(round(ncol))
            nrow = int(round(nrow))
            rlpix = ((ncol, nrow), )
            rarloc = w.pix_to_coords(rlpix)[0]
            adjra = rarloc[0] - targra
            adjdec = rarloc[1] - targdec
            adj_rad = math.sqrt(adjra**2 + adjdec**2)
            if adj_rad > maxadjr:
                offbrs = "Offset of brightest of %.2f exceeds maximum of %.2f" % (adj_rad, maxadjr)
                dbremfitsobj.add_notfound(dbcurs, obsind, targetname, filter, exptime, offbrs, notcurrf = notcurrentflat, apsize = tobj.get_aperture(mainap))
                if verbose:
                    print("Skipping", obsind, "target", targetname, maxbrs, file=sys.stderr)
                continue
            newf = FoundData(adj_rad, targetname, ncol, nrow, rarloc[0], rarloc[1], rarloc[0] - targra, rarloc[1] - targdec, tobj.get_aperture(mainap))
            clookup[newf] = newf

            # Now look for other objects (which don't include target)

            for possible in pruned_objlist:
                objra, objdec, m = possible
                adjra = objra
                adjdec = objdec
                # If we're tracking adjustments, adjust by average amount so far
                if accadjust:
                    adjra += np.mean([x.raadj for x in list(clookup.values())])
                    adjdec += np.mean([x.decadj for x in list(clookup.values())])
                objpixes = w.coords_to_pix(((adjra, adjdec),))[0]
                nearestobj = findnearest.findnearest(imagedata, objpixes, mainap, searchrad, med + sigma * nsigfind)
                if nearestobj is None:
                    continue
                ncol, nrow, nadu = nearestobj
                ncol = int(round(ncol))
                nrow = int(round(nrow))
                rlpix = ((ncol, nrow), )
                rarloc = w.pix_to_coords(rlpix)[0]
                adjra = rarloc[0] - objra
                adjdec = rarloc[1] - objdec
                adj_rad = math.sqrt(adjra**2 + adjdec**2)
                if adj_rad > maxadjr:
                    continue
                newf = FoundData(adj_rad, m.objname, ncol, nrow, rarloc[0], rarloc[1], adjra, adjdec, mainap)
                try:
                    oldf = clookup[newf]
                    if oldf.dist > newf.dist and oldf.objname != targetname:
                        clookup[newf] = newf
                except KeyError:
                    clookup[newf] = newf
        else:
            for possible in pruned_objlist:
                objra, objdec, m = possible
                adjra = objra
                adjdec = objdec
                # If we're tracking adjustments, adjust by average amount so far
                if accadjust and len(clookup) != 0:
                    adjra += np.mean([x.raadj for x in list(clookup.values())])
                    adjdec += np.mean([x.decadj for x in list(clookup.values())])
                objpixes = w.coords_to_pix(((adjra, adjdec),))[0]
                nearestobj = findnearest.findnearest(imagedata, objpixes, mainap, searchrad, med + sigma * nsigfind)
                if nearestobj is None:
                    continue
                if m.objname == targetname:
                    targobjpl = possible
                ncol, nrow, nadu = nearestobj
                ncol = int(round(ncol))
                nrow = int(round(nrow))
                rlpix = ((ncol, nrow), )
                rarloc = w.pix_to_coords(rlpix)[0]
                adjra = rarloc[0] - objra
                adjdec = rarloc[1] - objdec
                adj_rad = math.sqrt(adjra**2 + adjdec**2)
                if adj_rad > maxadjr:
                    continue
                newf = FoundData(adj_rad, m.objname, ncol, nrow, rarloc[0], rarloc[1], adjra, adjdec, mainap)
                try:
                    oldf = clookup[newf]
                    if oldf.dist > newf.dist and oldf.objname != targetname:
                        clookup[newf] = newf
                except KeyError:
                    clookup[newf] = newf

        if targobjpl is None:
            dbremfitsobj.add_notfound(dbcurs, obsind, targetname, filter, exptime, "Failed to find targer", notcurrf = False, apsize = mainap, searchrad = searchrad)
            if verbose:
                print("Skipping", obsind, "target", targetname, "not found in image", file=sys.stderr)
            continue

        for result in list(clookup.values()):
            ncol, nrow = w.abspix((result.col, result.row))
            dbremfitsobj.add_objident(dbcurs, obsind, targetname, result.name, filter, exptime, ncol, nrow, result.ra, result.dec, result.apsize, searchrad, notcurrf = False)
            nresults += 1

if verbose:
    print(nresults, "results added", file=sys.stderr)

sys.exit(0)
