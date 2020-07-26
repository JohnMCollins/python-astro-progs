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
import remget
import fitsops


def delfits(ind):
    """Delete any FITS file we are dumping"""
    global dbcurs, fitsdeleted

    if ind != 0:
        dbcurs.execute("DELETE FROM fitsfile WHERE ind=%d" % ind)
        dbcurs.execute("UPDATE obsinf SET ind=0 WHERE ind=%d" % ind)
        fitsdeleted += 1


parsearg = argparse.ArgumentParser(description='Check for duplicate files in observations', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg, libdir=False, tempdir=False)
resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)

dbase, dbcurs = remdefaults.opendb()

# First get list of duplicated files

dbcurs.execute("SELECT COUNT(*) AS n,ffname FROM obsinf WHERE rejreason IS NULL GROUP BY ffname HAVING n>1")
dbrows = dbcurs.fetchall()

fitsdeleted = 0
obsdeleted = 0

for nused, ffname in dbrows:
    if nused != 2:
        print(ffname, "used in", nused, "rows", file=sys.stderr)
        continue
    dbcurs.execute("SELECT ind,serial,object,dithID,filter,date_obs,exptime,gain,obsind FROM obsinf WHERE ffname=%s", ffname)
    usedlist = dbcurs.fetchall()
    if len(usedlist) != 2:
        print("expecting", ffname, "to be used twice not", len(usedlist), "times", file=sys.stderr)
        continue
    row1, row2 = usedlist
    r1ind, r1serial, r1obj, r1dith, r1filt, r1date, r1exptime, r1gain, r1obsind = row1
    r2ind, r2serial, r2obj, r2dith, r2filt, r2date, r2exptime, r2gain, r2obsind = row2
    if r1obj != r2obj or r1dith != r2dith or r1filt != r2filt or r1exptime != r2exptime or r1gain != r2gain or r1serial != r2serial:
        print("Fields do not correspnd for", ffname, file=sys.stderr)
        try:
            fhdr, fdata = fitsops.mem_get(remget.get_obs(ffname, r1dith != 0))
            obsdate = Time(fhdr['DATE-OBS']).datetime
            obsfilt = fhdr['FILTER']
            obsdith = fhdr['DITHID']
        except remget.RemGetError as e:
            print("Cannot fetch filel", ff, "error was", e.args[0], file=sys.stderr)
            dbcurs.execute("UPDATE obsinf SET rejreason='%s' WHERE obsind=%d OR obsind=%d" % ('FITS file unfetchable', r1obsind, r2obsind))
            delfits(r1ind)
            delfits(r2ind)
            continue
        except OSError as e:
            print("Cannot open FITS file from", ff, "error was", e.args[0], file=sys.stderr)
            dbcurs.execute("UPDATE obsinf SET rejreason='%s' WHERE obsind=%d OR obsind=%d" % ('FITS file could not open', r1obsind, r2obsind))
            delfits(r1ind)
            delfits(r2ind)
            continue
        except KeyError:
            print("Cannot find date in file", ff, file=sys.stderr)
            dbcurs.execute("UPDATE obsinf SET rejreason='%s' WHERE obsind=%d OR obsind=%d" % ('FITS file incomplete', r1obsind, r2obsind))
            delfits(r1ind)
            delfits(r2ind)
            continue
        if abs((r1date - obsdate).total_seconds()) > 1 or r1filt != obsfilt or r1dith != obsdith:
            dbcurs.execute("UPDATE obsinf SET rejreason='%s' WHERE obsind=%d" % ('Refers to wrong file', r1obsind))
            delfits(r1ind)
        if abs((r2date - obsdate).total_seconds()) > 1 or r2filt != obsfilt or r2dith != obsdith:
            dbcurs.execute("UPDATE obsinf SET rejreason='%s' WHERE obsind=%d" % ('Refers to wrong file', r2obsind))
            delfits(r2ind)
        continue
    delobsind = r2obsind
    if r1ind != r2ind:
        if r1ind == 0:
            delobsind = r1obsind
        elif r2ind != 0:
            delfits(r2ind)
    dbcurs.execute("DELETE FROM obsinf WHERE obsind=%d" % delobsind)
    obsdeleted += 1

dbase.commit()
print(fitsdeleted, "FITS files deleted", obsdeleted, "observations", file=sys.stderr)
