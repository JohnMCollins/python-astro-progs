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
parsearg = argparse.ArgumentParser(description='Recalculate sky level where we have already done moon phase etce', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('--database', type=str, default=mydbname, help='Database to use')
parsearg.add_argument('--year', type=int, help='Year to process default is current')
parsearg.add_argument('--month', type=int, help='Month to procees detault is current')
parsearg.add_argument('--filter', type=str, required=True, help='Filter to use')
parsearg.add_argument('--flatfile', type=str, help='Flat file to use', required=True)
parsearg.add_argument('--biasfile', type=str, help='Bias file to use', required=True)
parsearg.add_argument('--delfb', action='store_true', help='Delete flat and bias files at end')
parsearg.add_argument('--clipcrit', type=float, default=2.0, help='Number of std devs to flup treating as image data')
parsearg.add_argument('--tempdir', type=str, default=tmpdir, help='Temp directory to unload files')
parsearg.add_argument('--count', default=0, type=int, help='Display count every so many')
parsearg.add_argument('--description', type=str, help='Description for count')
resargs = vars(parsearg.parse_args())
mydbname = resargs['database']
year = resargs['year']
month = resargs['month']
tmpdir = resargs['tempdir']
flatfile = resargs['flatfile']
biasfile = resargs['biasfile']
filter = resargs['filter']
clipcrit = resargs['clipcrit']
count = resargs['count']
descr = resargs['description']
delfb = resargs['delfb']

if descr is not None:
    descr += ': '
else:
    descr = ''

if year is None or month is None:
    now = datetime.datetime.now()
    if year is None: year = now.year
    if month is None: month = now.month
    if year == now.year and month > now.month:
        year -= 1

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

daterange = "date_obs >= '%d-%d-01' AND date_obs <= date_sub(date_add('%d-%d-01', interval 1 month),interval 1 second)" % (year,month,year,month)
dbcurs.execute("SELECT obsinf.obsind,obsinf.ind,obscalc.skylevel,obscalc.skystd FROM obsinf INNER JOIN obscalc WHERE obsinf.obsind=obscalc.obsind and filter='" + filter + "' AND " + daterange)
rows = dbcurs.fetchall()
ndone = 0
nreached = 0
nupd = 0
todo = len(rows)
perc = 100.0 / todo

for obsind, fitsind, esky, estd in rows:
    nreached += 1
    if count != 0 and nreached % count == 0:
        print("%sReached %d of %d %.2f%%" % (descr, nreached, todo, nreached * perc), file=sys.stderr)
    if fitsind == 0:
        print("No FITS file for", obsind, file=sys.stderr)
        continue
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
    if skylevel == esky and stdd == estd:
        continue
    for tries in range(1,11):
        try:
            dbcurs.execute("UPDATE obscalc SET skylevel=%.6g,skystd=%.6g WHERE obsind=%d" % (skylevel,stdd,obsind))
            ndone += 1
            break
        except pymysql.err.OperationalError:
            time.sleep(tries)
            continue
    dbase.commit()

print(ndone, "observations altered", file=sys.stderr)
if delfb:
    try:
        os.unlink(flatfile)
    except PermissionError:
        print("Could not remove flat file", flatfile, file=sys.stderr)
    try:
        os.unlink(biasfile)
    except PermissionError:
        print("Could not remove bias file", biasfile, file=sys.stderr)
