#! /usr/bin/env python

# @Author: John M Collins <jmc>
# @Date:   2018-11-29T16:49:45+00:00
# @Email:  jmc@toad.me.uk
# @Filename: updairmass.py
# @Last modified by:   jmc
# @Last modified time: 2018-11-29T17:05:44+00:00

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

dbase = dbops.opendb('remfits')
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
        print >>sys.stderr, "Obsind", obsind, "DB hdr exptime", exptime, "FITS exptime", fexptime

    dbcurs.execute("UPDATE obsinf SET airmass=%.6g WHERE obsind=%d" % (fairmass, obsind))
    ffile.close()
    nfiles += 1

dbase.commit()
print >>sys.stderr, nfiles, "results added"
