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

tmpdir = remdefaults.get_tmpdir()
mydbname = remdefaults.default_database()
try:
    firstarg = sys.argv[1]
    if firstarg[0] == '-':
        parsearg = argparse.ArgumentParser(description='Update database fields from newly-loaded FITS files', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
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

# First get sides and update FITS files

dbcurs.execute("SELECT ind FROM fitsfile WHERE side IS NULL")
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

    ffshape = ffile[0].data.shape
    
    if  ffshape[0] != ffshape[-1]:
        side = 0
    else:
        side = ffshape[0]
    
    dbcurs.execute("UPDATE fitsfile SET side=%d WHERE ind=%d" % (side, ind))
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
    fgain = ffhdr['GAIN']

    if fexptime != exptime:
        print("Obsind", obsind, "DB hdr exptime", exptime, "FITS exptime", fexptime, file=sys.stderr)

    dbcurs.execute("UPDATE obsinf SET airmass=%.6g,gain=%.6g WHERE obsind=%d" % (fairmass, fgain, obsind))
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

dbcurs.execute("SELECT ind,iforbind FROM iforbinf WHERE gain IS NULL AND rejreason IS NULL AND ind!=0")
rows = dbcurs.fetchall()

nifb = 0

for fitsind, ind in rows:
           
    ffile = dbremfitsobj.getfits(dbcurs, fitsind)
    ffhdr = ffile[0].header
    fgain = ffhdr['GAIN']
    dbcurs.execute("UPDATE iforbinf SET gain=%.6g WHERE iforbind=%d" % (fgain, ind))
    ffile.close()
    nifb += 1

dbase.commit()

# Finally indiv flat or bias

print(nsides, "sides added", len(errorfiles), "errors", file=sys.stderr)
print(nfiles, "airmess/gains added", file=sys.stderr)
print(nmfb, "naster flat/bias/gains added", file=sys.stderr)
print(nifb, "individual flat/bias/gains added", file=sys.stderr)
