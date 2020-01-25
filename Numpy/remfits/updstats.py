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
parsearg = argparse.ArgumentParser(description='Quickly fix skew and kurt on dialy flats and minv maxv on bias', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('--database', type=str, default=mydbname, help='Database to use')
parsearg.add_argument('--tempdir', type=str, default=tmpdir, help='Temp directory to unload files')
parsearg.add_argument('--trimsides', type=int, default=100, help='Amount to trip off edges')
resargs = vars(parsearg.parse_args())
mydbname = resargs['database']
tmpdir = resargs['tempdir']
trimsides = resargs['trimsides']

try:
    os.chdir(tmpdir)
except FileNotFoundError:
    print("Unable to select temporary directory", tmpdir, file=sys.stderr)
    sys.exit(100)

dbase = dbops.opendb(mydbname)
dbcurs = dbase.cursor()

dbcurs.execute("SELECT ind,iforbind,typ FROM iforbinf WHERE minv IS NULL AND rejreason IS NULL AND ind!=0")
rows = dbcurs.fetchall()

nifb = 0
nrows = len(rows)

for fitsind, ind, typ in rows:
           
    ffile = dbremfitsobj.getfits(dbcurs, fitsind)
    fdat = ffile[0].data
    sqq = fdat.flatten()
    sqq = sqq[sqq != 0]
    nzfdat = trimarrays.trimzeros(fdat)
    tsfdat = nzfdat
    if trimsides > 0:
        tsfdat = nzfdat[trimsides:-trimsides, trimsides:-trimsides]
    dbcurs.execute("UPDATE iforbinf SET rows=%d,cols=%d,minv=%d,maxv=%d,median=%.8e,mean=%.8e,std=%.8e,skew=%.8e,kurt=%.8e WHERE iforbind=%d" % 
                   (nzfdat.shape[0], nzfdat.shape[1], sqq.min(), sqq.max(), np.median(tsfdat), tsfdat.mean(), tsfdat.std(), ss.skew(tsfdat, axis=None), ss.kurtosis(tsfdat, axis=None), ind))
    ffile.close()
    nifb += 1
    if nifb % 100 == 0:
        print("Got to image number", nifb, "of", nrows, file=sys.stderr)
        dbase.commit()

dbase.commit()

print(nifb, "individual flat/bias updated", file=sys.stderr)
