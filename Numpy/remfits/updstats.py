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
try:
    firstarg = sys.argv[1]
    if firstarg[0] == '-':
        parsearg = argparse.ArgumentParser(description='Quickly fix skew and kurt on dialy flats and minv maxv on bias', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parsearg.add_argument('--database', type=str, default=mydbname, help='Database to use')
        parsearg.add_argument('--tempdir', type=str, default=tmpdir, help='Temp directory to unload files')
        resargs = vars(parsearg.parse_args())
        mydbname = resargs['database']
        tmpdir = resargs['tempdir']
    else:
        mydbname = firstarg 
except IndexError:
        pass

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

for fitsind, ind, typ in rows:
           
    ffile = dbremfitsobj.getfits(dbcurs, fitsind)
    fdat = ffile[0].data
    if typ == 'flat':
        fdat = trimarrays.trimzeros(fdat)
    dbcurs.execute("UPDATE iforbinf SET rows=%d,cols=%d,minv=%d,maxv=%d,mean=%.8e,std=%.8e,skew=%.8e,kurt=%.8e WHERE iforbind=%d" % (fdat.shape[0], fdat.shape[1], fdat.min(), fdat.max(), fdat.mean(), fdat.std(), ss.skew(fdat, axis=None), ss.kurtosis(fdat, axis=None), ind))
    ffile.close()
    nifb += 1

dbase.commit()

# Finally indiv flat or bias

print(nifb, "individual flat/bias updated", file=sys.stderr)
