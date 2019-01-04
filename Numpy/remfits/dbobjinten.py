#! /usr/bin/env python3

# @Author: John M Collins <jmc>
# @Date:   2018-08-13T17:29:08+01:00
# @Email:  jmc@toad.me.uk
# @Filename: dbobjinten.py
# @Last modified by:   jmc
# @Last modified time: 2019-01-04T22:56:43+00:00

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
import dbobjinfo
import calcadus
import remgeom
import parsetime
import dbremfitsobj
import dbops

parsearg = argparse.ArgumentParser(description='Tabulate ADUs from FITS files', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('--mainap', type=int, default=6, help='main aperture radius')
parsearg.add_argument('--percentile', type=float, default=50.0, help='perecntile to subtract for sky level default median')

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)
autils.suppress_vo_warnings()

resargs = vars(parsearg.parse_args())

mainap = resargs['mainap']
percentile = resargs['percentile']

rg = remgeom.load()

dbase = dbops.opendb('remfits')
dbcurs = dbase.cursor()

sqrt12 = 1.0/math.sqrt(12.0)
lastmonth = -1
lastyear = -1
ndone = 0

# Get details of object once only if doing multiple pictures

objlookup = dict()

# Do everything by filter

for filter in 'griz':

    dbcurs.execute("SELECT obsind,ind,date_obs,exptime FROM obsinf WHERE filter='" + filter + "' ORDER BY date_obs")
    obslist = dbcurs.fetchall()

    for obsind, fitsind, when, exptime in obslist:

        # See if we've got any found objects for that obs and skip if not`

        fnd, nfnd = dbremfitsobj.get_find_results(dbcurs, obsind)
        if fnd == 0:
            continue

        # See if we've got sums for that percentile and skip if we have

        dbcurs.execute("SELECT COUNT(*) FROM aducalc WHERE obsind=" + str(obsind) + " AND percentile=" + "%.3f" % percentile)
        nsums = dbcurs.fetchall()
        if  nsums[0][0] != 0:
            continue

        # Get ourselves the flat and bias files for that month if it's not the same as last one

        cyear = when.year
        cmonth = when.month

        if cyear != lastyear or cmonth != lastmonth:
            flattab, biastab = dbremfitsobj.get_nearest_forbinf(dbcurs, cyear, cmonth)
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
            lastyear = cyear
            lastmonth = cmonth

        # Now get the image data and adjust by flat and bias files

        ffile = dbremfitsobj.getfits(dbcurs, fitsind)
        ffhdr = ffile[0].header
        imagedata = ffile[0].data.astype(np.float64)
        (imagedata, ) = trimarrays.trimto(fdat, imagedata)
        ffile.close()

        imagedata -= bdatc
        imagedata /= fdat
        errorarray = np.full(imagedata.shape, sqrt12) / fdat

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

        # Adjust to sky level

        skylevel = np.percentile(imagedata, percentile)
        imagedata -= skylevel
        mx = imagedata.max()

        # Now get list of finds for that obs

        dbcurs.execute("SELECT identind,target,objname,pixcol,pixrow FROM identobj WHERE obsind=" + str(obsind))
        finds = dbcurs.fetchall()

        for identind, target, objname, pixcol, pixrow in finds:
            try:
                objdets = objlookup[objname]
            except KeyError:
                objdets = dbobjinfo.get_object(dbcurs, objname)
                objlookup[objname] = objdets
            tcoords = w.relpix((pixcol, pixrow))
            trad = objdets.get_aperture(mainap)

            try:
                (tadus, terr) = calcadus.calcadus(imagedata, errorarray, tcoords, trad)
            except calcadus.calcaduerror as e:
                print("Error in adu calc obsind", obsind, e.args[0], file=sys.stderr)
                continue

            dbcurs.execute("INSERT INTO aducalc (identind,obsind,date_obs,target,objname,filter,exptime,percentile,skylevel,aducount,aduerr) VALUES (%d,%d,%s,%s,%s,%s,%.1f,%.3f,%.6g,%.6g,%.6g)" %
                    (identind, obsind, dbase.escape(when.isoformat()), dbase.escape(target), dbase.escape(objname), dbase.escape(filter), exptime, percentile, skylevel, tadus, terr))
            ndone += 1

        dbase.commit()

print(ndone, "results added", file=sys.stderr)
