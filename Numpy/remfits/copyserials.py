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


def insert_row(row):
    """Insert row into my copy of database"""
    global mycurs, destfields
    global rowsadded
    serial, radeg, decdeg, object, dithid, filter, dateobs, mjddate, exptime, fname, ffname = row
    destvals = []
    destvals.append("%d" % serial)
    destvals.append("%.16e" % radeg)
    destvals.append("%.16e" % decdeg)
    destvals.append("'" + object + "'")
    destvals.append("%d" % dithid)
    destvals.append("'" + filter + "'")
    destvals.append(dateobs.strftime("'%Y-%m-%d %H:%M:%S'"))
    destvals.append("%.16e" % mjddate)
    destvals.append("%.16e" % exptime)
    destvals.append("'" + fname + "'")
    destvals.append("'" + ffname + "'")
    destvals = "(" + ','.join(destvals) + ")"
    mycurs.execute(destfields + destvals)
    print("inserting serial", serial, file=sys.stderr)
    rowsadded += 1


def insert_fbrow(typ, ffname, row):
    """Insert row into my copy of database"""
    global mycurs, fbdestfields
    global fbrowsadded
    serial, filter, dateobs, mjddate, exptime, fname = row
    if filter not in 'griz':
        return
    destvals = []
    destvals.append("%d" % serial)
    destvals.append("'" + typ + "'")
    destvals.append("'" + filter + "'")
    destvals.append(dateobs.strftime("'%Y-%m-%d %H:%M:%S'"))
    destvals.append("%.16e" % mjddate)
    destvals.append("%.16e" % exptime)
    destvals.append("'" + fname + "'")
    destvals.append("'" + ffname + "'")
    destvals = "(" + ','.join(destvals) + ")"
    mycurs.execute(fbdestfields + destvals)
    fbrowsadded += 1


parsearg = argparse.ArgumentParser(description='Copy across serial numbers in obs/dark/flat files', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg, libdir=False, tempdir=False)
resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)

destfields = []
destfields.append('serial')
destfields.append('radeg')
destfields.append('decdeg')
destfields.append('object')
destfields.append('dithID')
destfields.append('filter')
destfields.append('date_obs')
destfields.append('mjdobs')
destfields.append('exptime')
destfields.append('fname')
destfields.append('ffname')
destfields = "INSERT INTO obsinf (" + ','.join(destfields) + ") VALUES"

fbdestfields = []
fbdestfields.append('serial')
fbdestfields.append('typ')
fbdestfields.append('filter')
fbdestfields.append('date_obs')
fbdestfields.append('mjdobs')
fbdestfields.append('exptime')
fbdestfields.append('fname')
fbdestfields.append('ffname')
fbdestfields = "INSERT INTO iforbinf (" + ','.join(fbdestfields) + ") VALUES"
fbobsfields = "SELECT serial,filter,date_obs,mjdobs,exptime,fname FROM "

rowsadded = 0
fbrowsadded = 0
rowsupdated = 0
fbrowsudated = 0
duplicates = 0
fbduplicates = 0
wrongfile = 0
fbwrongfile = 0

remdb = dbops.opendb('rdots')
remcurs = remdb.cursor()
mydbase, mycurs = remdefaults.opendb()

remcurs.execute("SELECT serial,radeg,decdeg,object,dithID,filter,date_obs,mjdobs,exptime,fname,ffname(date_obs,fname) AS ff FROM Obslog")
remrows = remcurs.fetchall()

for remrow in remrows:
    serial, radeg, decdeg, object, dithID, filter, date_obs, mjdobs, exptime, fname, ffname = remrow
    sflds = []
    sflds.append("dithID=%d" % dithID)
    sflds.append("filter='%s'" % filter)
    sflds.append("date_obs='%s'" % date_obs.strftime("%Y-%m-%d %H:%M:%S"))
    selection = " AND ".join(sflds)
    mycurs.execute("SELECT serial,fname,ffname FROM obsinf WHERE " + selection)
    mdbrows = mycurs.fetchall()
    if len(mdbrows) > 0:
        serdiff = False
        duplicates += len(mdbrows) - 1
        for ser, fn, ffn in mdbrows:
            if fn != fname or ffn != ffname:
                wrongfile += 1
                print("Serial", serial, "fname/ffname diff", fname, "-v-", fn, ffname, "-v-", ffn, file=sys.stederr)
            serdiff = serdiff or ser != serial
        if serdiff:
            mycurs.execute("UPDATE obsinf SET serial=%d WHERE %s" % (serial, selection))
            rowsupdated += len(mdbrows)
    else:
        insert_row(remrow)

mydbase.commit()

print("Obs files", rowsupdated, "rows updated", duplicates, "duplicates", rowsadded, "rows added", wrongfile, "wrong file", file=sys.stderr)
remdb.close()

remdb = dbops.opendb('rdotsquery')
remcurs = remdb.cursor()

remcurs.execute(fbobsfields + "Dark WHERE exptime=0")
remrows = remcurs.fetchall()
for remrow in remrows:
    serial, filter, date_obs, mjdobs, exptime, fname = remrow
    sflds = []
    sflds.append("typ='bias'")
    sflds.append("filter='%s'" % filter)
    sflds.append("date_obs='%s'" % date_obs.strftime("%Y-%m-%d %H:%M:%S"))
    ffname = "ImgsDBArchive/Dark/" + date_obs.strftime("%Y%m%d/") + fname + ".fits.gz"
    selection = " AND ".join(sflds)
    mycurs.execute("SELECT serial,fname,ffname FROM iforbinf WHERE " + selection)
    mdbrows = mycurs.fetchall()
    if len(mdbrows) > 0:
        serdiff = False
        fbduplicates += len(mdbrows) - 1
        for ser, fn, ffn in mdbrows:
            if fn != fname or ffn != ffname:
                fbwrongfile += 1
                print("Serial", serial, "fname/ffname diff", fname, "-v-", fn, ffname, "-v-", ffn, file=sys.stederr)
            serdiff = serdiff or ser != serial
        if serdiff:
            mycurs.execute("UPDATE iforbinf SET serial=%d WHERE %s" % (serial, selection))
            fbrowsudated += len(mdbrows)
    else:
        insert_fbrow('bias', ffname, remrow)

mydbase.commit()

remcurs.execute(fbobsfields + "Flat")
remrows = remcurs.fetchall()
for remrow in remrows:
    serial, filter, date_obs, mjdobs, exptime, fname = remrow
    sflds = []
    sflds.append("typ='flat'")
    sflds.append("filter='%s'" % filter)
    sflds.append("date_obs='%s'" % date_obs.strftime("%Y-%m-%d %H:%M:%S"))
    ffname = "ImgsDBArchive/Flat/" + date_obs.strftime("%Y%m%d/") + fname + ".fits.gz"
    selection = " AND ".join(sflds)
    mycurs.execute("SELECT serial,fname,ffname FROM iforbinf WHERE " + selection)
    mdbrows = mycurs.fetchall()
    if len(mdbrows) > 0:
        serdiff = False
        fbduplicates += len(mdbrows) - 1
        for ser, fn, ffn in mdbrows:
            if fn != fname or ffn != ffname:
                fbwrongfile += 1
                print("Serial", serial, "fname/ffname diff", fname, "-v-", fn, ffname, "-v-", ffn, file=sys.stederr)
            serdiff = serdiff or ser != serial
        if serdiff:
            mycurs.execute("UPDATE iforbinf SET serial=%d WHERE %s" % (serial, selection))
            fbrowsudated += len(mdbrows)
    else:
        insert_fbrow('flat', ffname, remrow)

mydbase.commit()

print("Flat/bias files", fbrowsudated, "rows updated", fbduplicates, "duplicates", fbrowsadded, "rows added", fbwrongfile, "wrong file", file=sys.stderr)
