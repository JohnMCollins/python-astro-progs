#! /usr/bin/env python

# @Author: John M Collins <jmc>
# @Date:   2018-08-13T17:29:08+01:00
# @Email:  jmc@toad.me.uk
# @Filename: objinten.py
# @Last modified by:   jmc
# @Last modified time: 2018-10-01T14:42:05+01:00

from astropy.io import fits
from astropy import wcs
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
from astropy.time import Time
import astroquery.utils as autils
import math
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
import parsetime
import remfitsobj

def pmjdate(arg):
    """Grab mjd from arg if possible"""
    if arg is None:
        return None
    try:
        t = Time(parsetime.parsetime(arg))
    except ValueError:
        print >>sys.stderr, "Could not understand time arg", arg
        sys.exit(50)
    return  t.mjd

class duplication(Exception):
    """Throw to get out of duplication loop"""
    pass

parsearg = argparse.ArgumentParser(description='Tabulate ADUs from FITS files', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('--libfile', type=str, default='~/lib/stellar_data', help='File to use for database')
parsearg.add_argument('--results', type=str, required=True, help='XML file of found objects updated with results')
parsearg.add_argument('--filter', type=str, help='Filter to select')
parsearg.add_argument('--firstdate', type=str, help='First date to prcoess')
parsearg.add_argument('--lastdate', type=str, help='Last date to process')
parsearg.add_argument('--trim', action='store_true', help='Trim trailing empty pixels')
parsearg.add_argument('--flatfile', type=str, help='Flat file to use')
parsearg.add_argument('--biasfile', type=str, help='Bias file to use')
parsearg.add_argument('--mainap', type=int, default=6, help='main aperture radius')
parsearg.add_argument('--skylevel', type=float, default=50.0, help='perecntile to subtract for sky level default median')

resargs = vars(parsearg.parse_args())
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
results = remfitsobj.RemobjSet()
try:
    results.loadfile(resultsfile)
except remfitsobj.RemObjError as e:
    print >>sys.stderr,  "Error loading results file", resultsfile, e.args[0]
    sys.exit(30)

target = results.targname
if target is None:
    print >>sys.stderr, "Results file", resultsfile, "does not have target"
    sys.exit(31)

firstdate = pmjdate(resargs['firstdate'])
lastdate = pmjdate(resargs['lastdate'])
filter = resargs['filter']

trimem = resargs['trim']

flatfile = resargs['flatfile']
biasfile = resargs['biasfile']

mainap = resargs['mainap']
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

# Get list of observations and found objects

oblist = results.getobslist(filter = filter, firstdate = firstdate, lastdate = lastdate)

if len(oblist) == 0:
    print >>sys.stderr, "Sorry no observations found try finding some more"
    sys.exit(1)

sqrt12 = 1.0/math.sqrt(12.0)

for ob in oblist:

    ffname = ob.filename
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
    errorarray = np.full(imagedata.shape, sqrt12)

    if flatfile is not None:
        imagedata /= fdat
        errorarray /= fdat

    w = wcscoord.wcscoord(ffhdr)

    if rg.trims.bottom is not None:
        imagedata = imagedata[rg.trims.bottom:]
        errorarray = errorarray[rg.trims.bottom:]
        w.set_offsets(yoffset=rg.trims.bottom)

    if rg.trims.left is not None:
        imagedata = imagedata[:,rg.trims.left:]
        errorarray = errorarray[:,rg.trims.left:]
        w.set_offsets(xoffset=rg.trims.left)

    if rg.trims.right is not None:
        imagedata = imagedata[:,0:-rg.trims.right]
        errorarray = errorarray[:,0:-rg.trims.right]

    # Adjust to sky level and store what we used

    perc = np.percentile(imagedata, skylevel)
    imagedata -= perc
    mx = imagedata.max()
    ob.percentile = skylevel
    ob.skylevel = perc

    tobj = ob.target
    tobjinf = objinf.get_object(target)

    tobj.apradius = tobjinf.get_aperture(mainap)
    try:
        (tadus, terr) = calcadus.calcadus(imagedata, errorarray, w.relpix((tobj.pixcol, tobj.pixrow)), tobj.apradius)
    except calcadus.calcaduerror as e:
        print >>sys.stderr, "Error in target file", ffname, e.args[0]
        continue
    tobj.aducount = tadus
    tobj.aduerror = terr

    for tobj in ob.objlist:
        tobjinf = objinf.get_object(tobj.objname)
        tobj.apradius = tobjinf.get_aperture(mainap)
        try:
            (tadus, terr) = calcadus.calcadus(imagedata, errorarray, w.relpix((tobj.pixcol, tobj.pixrow)), tobj.apradius)
        except calcadus.calcaduerror as e:
            print >>sys.stderr, "Error in obj", obj.objname, "file", ffname, e.args[0]
            continue
        tobj.aducount = tadus
        tobj.aduerror = terr

results.savefile()
