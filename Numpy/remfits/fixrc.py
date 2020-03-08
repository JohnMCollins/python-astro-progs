#! /usr/bin/env python3

# @Author: John M Collins <jmc>
# @Date:   2018-11-29T16:49:45+00:00
# @Email:  jmc@toad.me.uk
# @Filename: updairmass.py
# @Last modified by:   jmc
# @Last modified time: 2019-01-04T22:57:17+00:00

from astropy.io import fits
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
from astropy.time import Time
import astroquery.utils as autils
import scipy.stats as ss
import numpy as np
import os
import sys
import datetime
import string
import warnings
import dbobjinfo
import dbremfitsobj
import dbops
import remdefaults
import argparse
import trimarrays

tmpdir = remdefaults.get_tmpdir()
mydbname = remdefaults.default_database()
parsearg = argparse.ArgumentParser(description='Fix effective rows and columns on FIT| filess', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('--database', type=str, default=mydbname, help='Database to use')
parsearg.add_argument('--tempdir', type=str, default=tmpdir, help='Temp directory to unload files')
resargs = vars(parsearg.parse_args())
mydbname = resargs['database']
tmpdir = resargs['tempdir']

try:
    os.chdir(tmpdir)
except FileNotFoundError:
    print("Unable to select temporary directory", tmpdir, file=sys.stderr)
    sys.exit(100)

dbase = dbops.opendb(mydbname)
dbcurs = dbase.cursor()

# First get sides and update FITS files

dbcurs.execute("SELECT ind FROM fitsfile WHERE rpws IS NULL")
rows = dbcurs.fetchall()

nsides = 0
errorfiles = []

for (ind,) in rows:

    try:
        ffile = dbremfitsobj.getfits(dbcurs, ind)
    except OSError:
        errorfiles.append(ind)
        print("Could not get FITS file for ind", ind, file=sys.stderr)
        continue

    fdat = ffile[0].data
    nzfdat = trimarrays.trimzeros(trimarrays.trimnan(fdat))
    dbcurs.execute("UPDATE fitsfile SET rows=%d,cols=%d WHERE ind=%d" % (nzfdat.shape[0], nzfdat.shape[1], ind))
    ffile.close()
    nsides += 1
    if nsides % 20 == 0:
        dbase.commit()

dbase.commit()

# Finally indiv flat or bias

print(nsides, "rows or folumns added", len(errorfiles), "errors", file=sys.stderr)
