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

dbcurs.execute("SELECT obsind,ind,exptime FROM obsinf WHERE airmass IS NULL")
rows = dbcurs.fetchall()

nfiles = 0

for obsind, fitsind, exptime in rows:

    if fitsind <= 0:
        continue
    ffile = dbremfitsobj.getfits(dbcurs, fitsind)
    ffhdr = ffile[0].header
    fexptime = ffhdr['EXPTIME']
    fairmass = ffhdr['AIRMASS']

    if fexptime != exptime:
        print("Obsind", obsind, "DB hdr exptime", exptime, "FITS exptime", fexptime, file=sys.stderr)

    dbcurs.execute("UPDATE obsinf SET airmass=%.6g WHERE obsind=%d" % (fairmass, obsind))
    ffile.close()
    nfiles += 1

dbase.commit()
print(nfiles, "results added", file=sys.stderr)
