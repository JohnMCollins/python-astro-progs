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

parsearg = argparse.ArgumentParser(description='List entries in my database with serial=0 and see copy and master rdots ', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg, libdir=False, tempdir=False)
resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)

mydb, mydbcurs = remdefaults.opendb()

copydb = dbops.opendb("remcopy")
copycurs = copydb.cursor()
rdotsdb = dbops.opendb("rdots")
rdotscurs = rdotsdb.cursor()

mydbcurs.execute("SELECT obsind,filter,date_obs,dithID,fname,ffname FROM obsinf WHERE serial=0 AND rejreason IS NULL")
s0rows = mydbcurs.fetchall()

hadcopy = hadrdots = hasfile = nofile = 0
for obsind, filter, date_obs, dithID, fname, ffname in s0rows:
    sd = date_obs.strftime("%Y-%m-%d %H:%M:%S")
    copycurs.execute("SELECT serial,fname FROM Obslog_myro WHERE filter='%s' AND date_obs='%s' AND dithID=%d" % (filter, sd, dithID))
    copyrows = copycurs.fetchall()
    rdotscurs.execute("SELECT serial,fname FROM Obslog WHERE filter='%s' AND date_obs='%s' AND dithID=%d" % (filter, sd, dithID))
    rdotsrows = rdotscurs.fetchall()
    hadcopy += len(copyrows)
    hadrdots += len(rdotsrows)
    try:
        fhdr, fdata = fitsops.mem_get(remget.get_obs(ffname, dithID != 0))
        obsdate = Time(fhdr['DATE-OBS']).datetime.strftime("%Y-%m-%d %H:%M:%S")
        hasfile += 1
        obsind = 0
    except remget.RemGetError as e:
        obsdate = "No file readable"
        nofile += 1
    except OSError as e:
        obsdate = "File error"
        nofile += 1
    except KeyError:
        obsdate = "Mp date"
        nofile += 1
    print(filter, sd, dithID, ffname, obsdate, sep="\t")
    if obsind != 0:
        mydbcurs.execute("DELETE FROM obsinf WHERE obsind=%d" % obsind)

print(hadcopy, "In copy", hadrdots, "in rdots", hasfile, "has file", nofile, "no file")
mydb.commit()
