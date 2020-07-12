#! /usr/bin/env python3

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

parsearg = argparse.ArgumentParser(description='Check for duplicate files in observations', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(libdir=False, tempdir=False)
parsearg.add_argument('--trimsides', type=int, default=100, help='Amount to trip off edges')
resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
trimsides = resargs['trimsides']

dbase, dbcurs = remdefaults.opendb()

# First get list of duplicated files

dbcurs.execute("SELECT COUNT(*) AS n,fname FROM obsinf GROUP BY fname HAVING n!=1")
dbrows = dbcurs.fetchall()

for nused, fname in dbrows:
    dbcurs.execute("SELECT ind,object,dithID,filter,date_obs,exptime,gain,obsind FROM obsinf WHERE fname=%s", fname)
    usedlist = dbcurs.fetchall()

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
    ffshape = fdat.shape

    if  ffshape[0] != ffshape[-1]:
        side = 0
    else:
        side = ffshape[0]

    nzfdat = trimarrays.trimzeros(trimarrays.trimnan(fdat))
    dbcurs.execute("UPDATE fitsfile SET side=%d,rows=%d,cols=%d WHERE ind=%d" % (side, nzfdat.shape[0], nzfdat.shape[1], ind))
    ffile.close()
    nsides += 1
    if nsides % 20 == 0:
        dbase.commit()

for find in errorfiles:
    dbremfitsobj.badfitsfile(dbcurs, find)

dbase.commit()

# Fix gain and airmass, check exp time in observations

dbcurs.execute("SELECT obsind,ind,exptime FROM obsinf WHERE ind!=0 AND rejreason IS NULL AND (airmass IS NULL OR gain IS NULL)")
rows = dbcurs.fetchall()

nfiles = 0

for obsind, fitsind, exptime in rows:

    ffile = dbremfitsobj.getfits(dbcurs, fitsind)
    ffhdr = ffile[0].header
    fexptime = ffhdr['EXPTIME']
    fairmass = ffhdr['AIRMASS']
    moonphase = ffhdr['MOONPHAS']
    moondist = ffhdr['MOONDIST']
    fgain = ffhdr['GAIN']

    if fexptime != exptime:
        print("Obsind", obsind, "DB hdr exptime", exptime, "FITS exptime", fexptime, file=sys.stderr)

    fdat = ffile[0].data
    sqq = fdat.flatten()
    sqq = sqq[sqq != 0]
    nzfdat = trimarrays.trimzeros(fdat)
    tsfdat = nzfdat
    if trimsides > 0:
        tsfdat = nzfdat[trimsides:-trimsides, trimsides:-trimsides]

    dbcurs.execute("UPDATE obsinf SET airmass=%.6g,gain=%.6g,moonphase=%.6g,moondist=%.6g,rows=%d,cols=%d,minv=%d,maxv=%d,sidet=%d,median=%.8e,mean=%.8e,std=%.8e,skew=%.8e,kurt=%.8e WHERE obsind=%d" %
                    (fairmass, fgain, moonphase, moondist, nzfdat.shape[0], nzfdat.shape[1], sqq.min(), sqq.max(), trimsides, np.median(tsfdat), tsfdat.mean(), tsfdat.std(), ss.skew(tsfdat, axis=None), ss.kurtosis(tsfdat, axis=None), obsind))
    ffile.close()
    nfiles += 1

dbase.commit()

# Repeat for master flats and biases

dbcurs.execute("SELECT year,month,filter,typ,fitsind FROM forbinf WHERE gain IS NULL AND rejreason IS NULL AND fitsind!=0")
rows = dbcurs.fetchall()

nmfb = 0

for year, month, filter, typ, fitsind in rows:

    ffile = dbremfitsobj.getfits(dbcurs, fitsind)
    ffhdr = ffile[0].header
    fgain = ffhdr['GAIN']
    dbcurs.execute("UPDATE forbinf SET gain=%.6g WHERE filter='%s' AND typ='%s' AND year=%d AND month=%d" % (fgain, filter, typ, year, month))
    ffile.close()
    nmfb += 1

dbase.commit()

# Finally indiviaul flag and bias

dbcurs.execute("SELECT ind,iforbind,typ FROM iforbinf WHERE (sidet!=%d OR gain IS NULL) AND rejreason IS NULL AND ind!=0" % trimsides)
rows = dbcurs.fetchall()

nifb = 0

for fitsind, ind, typ in rows:

    ffile = dbremfitsobj.getfits(dbcurs, fitsind)
    ffhdr = ffile[0].header
    fgain = ffhdr['GAIN']
    fdat = ffile[0].data
    sqq = fdat.flatten()
    sqq = sqq[sqq != 0]
    nzfdat = trimarrays.trimzeros(fdat)
    tsfdat = nzfdat
    if trimsides > 0:
        tsfdat = nzfdat[trimsides:-trimsides, trimsides:-trimsides]
    dbcurs.execute("UPDATE iforbinf SET gain=%.6g,rows=%d,cols=%d,minv=%d,maxv=%d,sidet=%d,median=%.8e,mean=%.8e,std=%.8e,skew=%.8e,kurt=%.8e WHERE iforbind=%d" %
                   (fgain, nzfdat.shape[0], nzfdat.shape[1], sqq.min(), sqq.max(),
                    trimsides, np.median(tsfdat), tsfdat.mean(), tsfdat.std(),
                    ss.skew(tsfdat, axis=None), ss.kurtosis(tsfdat, axis=None), ind))
    ffile.close()
    nifb += 1

dbase.commit()

# Finally indiv flat or bias

print(nsides, "sides added", len(errorfiles), "errors", file=sys.stderr)
print(nfiles, "airmess/gains added", file=sys.stderr)
print(nmfb, "naster flat/bias/gains added", file=sys.stderr)
print(nifb, "individual flat/bias/gains added", file=sys.stderr)
