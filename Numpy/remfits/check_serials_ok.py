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
import mydateutil

parsearg = argparse.ArgumentParser(description='Check serial numbers in obs/dark/flat files', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg, libdir=False, tempdir=False)
resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)

badobs = badbias = badflat = 0

remdb = dbops.opendb('rdots')
remcurs = remdb.cursor()
mydbase, mycurs = remdefaults.opendb()

mycurs.execute("SELECT serial,dithID,filter,date_obs,object FROM obsinf WHERE dithID=0 and object regexp '(prox|barn|ross)' and rejreason IS NULL")
serial_dith = mycurs.fetchall()

nfobj = dict()
try:
    for ser, dith, filter, date_obs, obj in serial_dith:
        remcurs.execute("SELECT COUNT(*) FROM Obslog WHERE serial=%d AND dithID=%d" % (ser, dith))
        nr = remcurs.fetchall()
        if nr[0][0] == 0:

            badobs += 1
            try:
                nfobj[obj] += 1
            except KeyError:
                nfobj[obj] = 1
            remcurs.execute("SELECT serial FROM Obslog WHERE date_obs=%s AND filter='" + filter + "' AND dithID=" + str(dith), mydateutil.mysql_datetime(date_obs))
            fixes = remcurs.fetchall()
            if len(fixes) != 1:
                print("%-8d %2d %s %s %s" % (ser, dith, filter, mydateutil.mysql_datetime(date_obs), obj))
                # print("Serial %d dithID %d filter %s date %s object %s not found in obs no new serial" % (ser, dith, filter, mydateutil.mysql_datetime(date_obs), obj))
            else:
                newser = fixes[0][0]
                print("Serial %d dithID %d filter %s date %s object %s changed to %d" % (ser, dith, filter, mydateutil.mysql_datetime(date_obs), obj, newser))
        else:
            pass
            # print("Serial %d dithID %d filter %s date %s object %s in obs OK" % (ser, dith, filter, mydateutil.mysql_datetime(date_obs), obj))
except KeyboardInterrupt:
    sys.exit(0)
remdb.close()

remdb = dbops.opendb('rdotsquery')
remcurs = remdb.cursor()

mycurs.execute("SELECT serial FROM iforbinf WHERE typ='bias' AND rejreason IS NULL")
serialsb = mycurs.fetchall()

for ser in serialsb:
    remcurs.execute("SELECT COUNT(*) FROM Dark WHERE serial=%d AND exptime=0" % ser)
    nr = remcurs.fetchall()
    if nr[0][0] == 0:
        print("Serial %d not found in Dark" % ser)
        badbias += 1

mycurs.execute("SELECT serial FROM iforbinf WHERE typ='flat' AND rejreason IS NULL")
serialsf = mycurs.fetchall()

for ser in serialsf:
    remcurs.execute("SELECT COUNT(*) FROM Flat WHERE serial=%d" % ser)
    nr = remcurs.fetchall()
    if nr[0][0] == 0:
        print("Serial %d not found in Flat" % ser)
        badflat += 1

if badobs + badbias + badflat == 0:
    print("Found nothing amiss")
else:
    if badobs != 0:
        print(badobs, "Bad observations out of", len(serial_dith), "%.2f%%" % (100.0 * badobs / len(serial_dith)))
        for obj in sorted(nfobj.keys()):
            print("%s\t%d" % (obj, nfobj[obj]))
    if badbias != 0:
        print(badbias, "Bad bias out of", len(serialsb), "%.2f%%" % 100.0 * badbias / len(serialsb))
    if badflat != 0:
        print(badflat, "Bad flat out of", len(serialsf), "%.2f%%" % 100.0 * badflat / len(serialsf))
