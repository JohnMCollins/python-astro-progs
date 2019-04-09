#! /usr/bin/env python3

# @Author: John M Collins <jmc>
# @Date:   2018-08-25T10:48:07+01:00
# @Email:  jmc@toad.me.uk
# @Filename: imfindobj.py
# @Last modified by:   jmc
# @Last modified time: 2019-01-04T22:51:33+00:00

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
import remdefaults
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

parsearg = argparse.ArgumentParser(description='Find pixels which are negtive after bias files applied', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('--database', type=str, default=remdefaults.default_database(), help='Database to use')
parsearg.add_argument('--year', type=int, help='Year to scan (default current year)')
parsearg.add_argument('--month', type=int, help='Month to scan (default current month)')
parsearg.add_argument('--tempdir', type=str, help='Temp directory to unload files default CWD')
parsearg.add_argument('--prefix', type=str, default='neg', help='prefix for file names')

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

dbname = resargs['database']

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

mydb = dbops.opendb(dbname)
dbcurs = mydb.cursor()

# See if targetname is the object name, otherwise look up as alias

flattab, biastab = dbremfitsobj.get_nearest_forbinf(dbcurs, year, month)

for filter in 'girz':

    # First get flat and bias files for month

    ftab = flattab[filter]
    btab = biastab[filter]

    ff = dbremfitsobj.getfits(dbcurs, ftab.fitsind)
    fdat = trimarrays.trimnan(ff[0].data)
    ffrows, ffcols = fdat.shape
    ftab.fitsimage = fdat
    ff.close()

    bf = dbremfitsobj.getfits(dbcurs, btab.fitsind)
    bdat = bf[0].data
    bdat = bdat[0:ffrows,0:ffcols]
    bdat = bdat.astype(np.float64)
    btab.fitsimage = bdat
    bf.close()

datesel = "'%.4d-%.2d-01'" % (year, month)
datesel = "date_obs>=" + datesel + " AND date_obs < DATE_ADD(" + datesel + ",INTERVAL 1 MONTH)"
dbcurs.execute("SELECT obsind,ind,object,date_obs,filter FROM obsinf WHERE " + datesel + " ORDER BY date_obs")
obstab = dbcurs.fetchall()

for obst in obstab:
    
    obsind, fitsind, object, date_obs,filter = obst
    
    if filter not in 'griz':
        continue

    ffile = dbremfitsobj.getfits(dbcurs, fitsind)
    
    ffhdr = ffile[0].header
    imagedata = ffile[0].data.astype(np.float64)
    fdat = flattab[filter].fitsimage
    (imagedata, ) = trimarrays.trimto(fdat, imagedata)
    ffile.close()

    imagedata -= biastab[filter].fitsimage
    imagedata /= fdat

    negs = np.count_nonzero(imagedata < 0.0)
    tot = np.multiply(*imagedata.shape)
    sigma = imagedata.std()
    oversigma = np.count_nonzero(imagedata <= -sigma)
    print("%-14s%7d %s%7d%6d%6d%6.2f%10.2f%10.2f" % (object, obsind, filter, tot, negs, oversigma, 100.0 * negs/tot, imagedata.min(), sigma))

sys.exit(0)
