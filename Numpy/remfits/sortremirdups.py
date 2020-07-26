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
import re

filep = re.compile('File\s+(.*\.gz).*of\s+(\d\d)/(\d\d)/(\d\d\d\d)\s+@\s+(\d\d):(\d\d):(\d+\d)')
serp = re.compile('\s+(\d+)\s+(\d\d)/(\d\d)/(\d\d\d\d)\s+@\s+(\d\d):(\d\d):(\d+\d)\s+(Same|Different)\s+date')

parsearg = argparse.ArgumentParser(description='Run through table of REMIR dups and flag incorrect ones', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg, libdir=False, tempdir=False)
parsearg.add_argument('--flagfile', type=str, required=True, help='File list showing valid and invalid serials')
resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
flagfile = resargs['flagfile']

try:
    ff = open(flagfile, 'rt')
except OSError as e:
    print("Cannot open", flagfile, "error was", e.args[1])
    sys.exit(10)

setups = []

while 1:
    samedat = None
    diffdat = None
    fline = ff.readline()
    if len(fline) == 0:
        break
    if len(fline) == 1:
        continue
    m = filep.match(fline)
    if m is None:
        print("Failed to match line for file name was", fline, file=sys.stderr)
        sys.exit(11)
    fname, day, month, year, hour, minute, second = m.groups()
    filedat = datetime.datetime(day=int(day), month=int(month), year=int(year), hour=int(hour), minute=int(minute), second=int(second))
    for lsel in ("2nd", "3rd"):
        fline = ff.readline()
        if len(fline) == 0:
            print("Expecting to read", lsel, "line but hit EOF", file=sys.stderr)
            sys.exit(12)
        m = serp.match(fline)
        if m is None:
            print("Failed to match line for", lsel, "line was", fline, file=sys.stderr)
            sys.exit(13)
        serial, day, month, year, hour, minute, second, sd = m.groups()
        dat = datetime.datetime(day=int(day), month=int(month), year=int(year), hour=int(hour), minute=int(minute), second=int(second))
        if sd == 'Same':
            if samedat is not None:
                print("Already got same date for", lsel, "line was", fline, file=sys.stderr)
                sys.exit(14)
            sameser = int(serial)
            samedat = dat
        else:
            if diffdat is not None:
                print("Already got same date for", lsel, "line was", fline, file=sys.stderr)
                sys.exit(14)
            diffser = int(serial)
            diffdat = dat
    setups.append((sameser, diffser, samedat, diffdat, fname))

dbase, dbcurs = remdefaults.opendb()

donealready = 0
fitsdeleted = 0
obsrejected = 0

for sameser, diffser, samedat, diffdat, fname in setups:

    dd = diffdat.strftime("%Y-%m-%d %H:%M:%S")
    dbcurs.execute("SELECT ind,obsind FROM obsinf WHERE serial=%d AND date_obs='%s' AND rejreason IS NULL" % (diffser, dd))
    diffrows = dbcurs.fetchall()
    if len(diffrows) == 0:
        donealready += 1
        continue
    for ind, obsind in diffrows:
        if ind != 0:
            dbcurs.execute("DELETE FROM fitsfile WHERE ind=%d" % ind)
            fitsdeleted += 1
        dbcurs.execute("UPDATE obsinf SET ind=0,rejreason='Refers to wrong file' WHERE obsind=%d" % obsind)
        obsrejected += 1

dbase.commit()
if donealready > 0:
    print(donealready, "done already", file=sys.stderr)
if fitsdeleted > 0:
    print(fitsdeleted, "FITS files deleted", file=sys.stderr)
if obsrejected > 0:
    print(obsrejected, "Obs files marked as rejected", file=sys.stderr)
