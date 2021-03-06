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
import os.path
import sys
import datetime
import string
import dbobjinfo
import dbremfitsobj
import dbops
import remdefaults
import argparse
import ephem
import trimarrays
import remgeom
import pymysql
import time

tmpdir = remdefaults.get_tmpdir()
mydbname = remdefaults.default_database()
parsearg = argparse.ArgumentParser(description='Check moon phase and distance and compare with FITS file', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('ids', type=int, nargs='+', help='Obs ID numbers')
parsearg.add_argument('--database', type=str, default=mydbname, help='Database to use')
parsearg.add_argument('--flatfile', type=str, help='Flat file to use', required=True)
parsearg.add_argument('--biasfile', type=str, help='Bias file to use', required=True)
parsearg.add_argument('--delfb', action='store_true', help='Delete flat and bias files at end')
parsearg.add_argument('--clipcrit', type=float, default=2.0, help='Number of std devs to flup treating as image data')
parsearg.add_argument('--replace', action='store_true', help='Replace existing calculations')
parsearg.add_argument('--tempdir', type=str, default=tmpdir, help='Temp directory to unload files')
parsearg.add_argument('--count', default=0, type=int, help='Display count every so many')
parsearg.add_argument('--description', type=str, help='Description for count')
resargs = vars(parsearg.parse_args())
idlist = resargs['ids']
mydbname = resargs['database']
tmpdir = resargs['tempdir']
flatfile = resargs['flatfile']
biasfile = resargs['biasfile']
clipcrit = resargs['clipcrit']
replace = resargs['replace']
count = resargs['count']
descr = resargs['description']
delfb = resargs['delfb']

if descr is not None:
    descr += ': '
else:
    descr = ''

rg = remgeom.load()

try:
    ff = fits.open(flatfile)
    fdat = trimarrays.trimnan(ff[0].data)
    ffrows, ffcols = fdat.shape
    ff.close()
except (FileNotFoundError, PermissionError):
    print("Cannot open flat file", flatfile, file=sys.stderr)
    sys.exit(90)

try:
    bf = fits.open(biasfile)
    bdat = bf[0].data
    (bdat, ) = trimarrays.trimto(fdat, bdat)
    bdat = bdat.astype(np.float64)
    bf.close()
except (FileNotFoundError, PermissionError):
    print("Cannot open bias file", biasfile, file=sys.stderr)
    sys.exit(91)

flatfile = os.path.abspath(flatfile)
biasfile = os.path.abspath(biasfile)
try:
    os.chdir(tmpdir)
except FileNotFoundError:
    print("Unable to select temporary directory", tmpdir, file=sys.stderr)
    sys.exit(100)

fdattr, bdat = rg.apply_trims(None, fdat, bdat)
fmean = fdattr.mean()

dbase = dbops.opendb(mydbname)
dbcurs = dbase.cursor()

lasilla = EarthLocation.of_site('lasilla')
obsls = ephem.Observer()
obsls.lat = lasilla.lat.to(u.radian).value
obsls.lon = lasilla.lon.to(u.radian).value
obsls.elevation = lasilla.height.value

ndone = 0
nreached = 0
todo = len(idlist)
perc = 100.0 / todo

for oid in idlist:
    nreached += 1
    if count != 0 and nreached % count == 0:
        print("%sReached %d of %d %.2f%%" % (descr, nreached, todo, nreached * perc), file=sys.stderr)
    if not replace:
        dbcurs.execute("SELECT COUNT(*) FROM obscalc WHERE obsind=%d" % oid)
        rows = dbcurs.fetchall()
        if rows[0][0] > 0:
            continue
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
    visible = m.alt >= 0;
    moonpos = SkyCoord(ra = m.g_ra * u.rad, dec = m.g_dec * u.rad)
    sep = moonpos.separation(objpos).to(u.deg).value
    moonphase = m.moon_phase
    ff = dbremfitsobj.getfits(dbcurs, fitsind)
    imagedata = ff[0].data
    (imagedata, ) = trimarrays.trimto(fdat, imagedata)
    imagedata = imagedata.astype(np.float64)
    ff.close()
    (imagedata, ) = rg.apply_trims(None, imagedata)
    imagedata -= bdat
    imagedata *= fmean
    imagedata /= fdattr
    imagedata = imagedata.flatten()
    med = np.median(imagedata)
    stdd = imagedata.std()
    imagedata = imagedata[imagedata <= med + clipcrit * stdd]
    if len(imagedata) < 100:
        print("Obs id", oid, "not enough data left after clipping", file=sys.stderr)
        continue
    skylevel = imagedata.mean()
    stdd = imagedata.std()
    for tries in range(1,11):
        try:
            if replace:
                dbcurs.execute("DELETE FROM obscalc WHERE obsind=%d" % oid)
            dbcurs.execute("INSERT INTO obscalc (obsind,moonvis,moonphase,moondist,skylevel,skystd) VALUES (%d,%d,%.6g,%.6g,%.6g,%.6g)" %(oid,visible,moonphase,sep,skylevel,stdd))
            ndone += 1
            break
        except pymysql.err.OperationalError:
            time.sleep(tries)
            continue
    dbase.commit()

print(ndone, "observations processed", file=sys.stderr)
if delfb:
    try:
        os.unlink(flatfile)
    except PermissionError:
        print("Could not remove flat file", flatfile, file=sys.stderr)
    try:
        os.unlink(biasfile)
    except PermissionError:
        print("Could not remove bias file", biasfile, file=sys.stderr)
