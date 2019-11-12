#! /usr/bin/env python3

# @Author: John M Collins <jmc>
# @Date:   2018-11-29T16:49:45+00:00
# @Email:  jmc@toad.me.uk
# @Filename: updairmass.py
# @Last modified by:   jmc
# @Last modified time: 2019-01-04T22:57:17+00:00

from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
import warnings
warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)
from astropy.io import fits
from astropy.time import Time
from astropy.coordinates import EarthLocation, SkyCoord, AltAz
import astroquery.utils as autils
import astropy.units as u
import numpy as np
import os
import sys
import datetime
import string
import dbobjinfo
import dbremfitsobj
import dbops
import remdefaults
import argparse
import ephem

tmpdir = remdefaults.get_tmpdir()
mydbname = remdefaults.default_database()
parsearg = argparse.ArgumentParser(description='Check moon phase and distance and compare with FITS file', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('ids', type=int, nargs='+', help='Obs ID numbers')
parsearg.add_argument('--database', type=str, default=mydbname, help='Database to use')
parsearg.add_argument('--tempdir', type=str, default=tmpdir, help='Temp directory to unload files')
resargs = vars(parsearg.parse_args())
idlist = resargs['ids']
mydbname = resargs['database']
tmpdir = resargs['tempdir']

try:
    os.chdir(tmpdir)
except FileNotFoundError:
    print("Unable to select temporary directory", tmpdir, file=sys.stderr)
    sys.exit(100)

dbase = dbops.opendb(mydbname)
dbcurs = dbase.cursor()

lasilla = EarthLocation.of_site('lasilla')
obsls = ephem.Observer()
obsls.lat = lasilla.lat.to(u.radian).value
obsls.lon = lasilla.lon.to(u.radian).value
obsls.elevation = lasilla.height.value

for oid in idlist:
    dbcurs.execute("SELECT object,ind,date_obs,moonphase,moondist FROM obsinf WHERE obsind=%d" % oid)
    rows = dbcurs.fetchall()
    if len(rows) == 0:
        print("No obs with id", oid, "found", file=sys.stderr)
        continue
    obj, fitsind, date, rmp, rmd = rows[0]
    if fitsind == 0:
        print("No FITS file for", oid, file=sys.stderr)
        continue
    if rmp is None or rmd is None:
        print("No existing moon params for", oid, file=sys.stderr)
    try:
        targname = dbobjinfo.get_targetname(dbcurs, obj)
    except dbobjinfo.ObjDataError as e:
        print("cannot find targ", obj, "error was", e.args[0], file=sys.stderr)
        continue
    objdata = dbobjinfo.get_object(dbcurs, targname)
    rightasc = objdata.get_ra(date)
    decl = objdata.get_dec(date)
    objpos = SkyCoord(ra=rightasc*u.deg, dec=decl*u.deg)
    myaa = AltAz(location=lasilla, obstime=date)
    objaa = objpos.transform_to(myaa)
    obsls.date = date
    m = ephem.Moon(obsls)
    if m.alt < 0:
        print("I think the moon is below horizon")
    sep = ephem.separation((m.az, m.alt), (objaa.az.to(u.rad).value, objaa.alt.to(u.rad).value)).real/np.pi*180.0
    nowt = ephem.date(date)
    prevnm = ephem.previous_new_moon(date)
    nextnm = ephem.next_new_moon(date)
    midp = (prevnm + nextnm) / 2.0
    if nowt >= midp:
        moonphase = (nextnm - nowt) / (nextnm - midp)
    else:
        moonphase = (nowt - prevnm) / (midp - prevnm)
    print("Oid", oid, "Calc phase", moonphase, "sep", sep, "given phase", rmp, "given sep", rmd)
