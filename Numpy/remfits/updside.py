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
import sys
import datetime
import string
import warnings
import dbobjinfo
import dbremfitsobj
import dbops

mydbname = 'remfits'
try:
        mydbname = sys.argv[1]
except IndexError:
        pass

dbase = dbops.opendb(mydbname)
dbcurs = dbase.cursor()

dbcurs.execute("SELECT ind FROM fitsfile WHERE side IS NULL")
rows = dbcurs.fetchall()

nfiles = 0
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
    nfiles += 1
    if nfiles % 20 == 0:
        dbase.commit()

for find in errorfiles:
    dbremfitsobj.badfitsfile(dbcurs, find)

dbase.commit()
print(nfiles, "sides added", len(errorfiles), "errors", file=sys.stderr)
