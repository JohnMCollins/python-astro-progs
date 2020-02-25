#! /usr/bin/env python3

# @Author: John M Collins <jmc>
# @Date:   2018-11-29T16:49:45+00:00
# @Email:  jmc@toad.me.uk
# @Filename: updairmass.py
# @Last modified by:   jmc
# @Last modified time: 2019-01-04T22:57:17+00:00

from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
import warnings
warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)
from astropy.io import fits
from astropy.time import Time
from astropy.coordinates import EarthLocation, SkyCoord, AltAz
import astroquery.utils as autils
import astropy.units as u
import numpy as np
import os
import os.path
import sys
import datetime
import string
import dbobjinfo
import dbremfitsobj
import dbops
import remdefaults
import argparse
import ephem
import pymysql
import time


def get_moonpars(targ, date):
    """Get moon parameters we want returning as tuple visibiity, phase and separation"""

    global dbcurs, obsls

    objdata = dbobjinfo.get_object(dbcurs, targ)
    rightasc = objdata.get_ra(date)
    decl = objdata.get_dec(date)
    objpos = SkyCoord(ra=rightasc * u.deg, dec=decl * u.deg)
    myaa = AltAz(location=lasilla, obstime=date)
    objaa = objpos.transform_to(myaa)
    obsls.date = date
    m = ephem.Moon(obsls)
    visible = m.alt >= 0;
    moonpos = SkyCoord(ra=m.g_ra * u.rad, dec=m.g_dec * u.rad)
    sep = moonpos.separation(objpos).to(u.deg).value
    moonphase = m.moon_phase
    return (visible, moonphase, sep)

# Remember things we've looked up


targlookup = dict()
targerror = dict()


def get_target(name):
    """Get target name from name in obsinf"""

    global targlookup, targerror, dbcurs
    try:
        return targlookup[name]
    except KeyError:
        pass
    try:
       targname = dbobjinfo.get_targetname(dbcurs, obj)
    except dbobjinfo.ObjDataError as e:
        if obj not in targerror:
            print("cannot find target", obj, "error was", e.args[0], file=sys.stderr)
            targerror[obj] = 1
        return None
    targlookup[name] = targname
    return targname


mydbname = remdefaults.default_database()
parsearg = argparse.ArgumentParser(description='Check moon phase and distance for each obs', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('--database', type=str, default=mydbname, help='Database to use')
parsearg.add_argument('--count', default=0, type=int, help='Display count every so many')
parsearg.add_argument('--description', type=str, help='Description for count')
resargs = vars(parsearg.parse_args())
mydbname = resargs['database']
count = resargs['count']
descr = resargs['description']

if descr is not None:
    descr += ': '
else:
    descr = ''

dbase = dbops.opendb(mydbname)
dbcurs = dbase.cursor()

lasilla = EarthLocation.of_site('lasilla')
obsls = ephem.Observer()
obsls.lat = lasilla.lat.to(u.radian).value
obsls.lon = lasilla.lon.to(u.radian).value
obsls.elevation = lasilla.height.value

# First fetch rows where we haven't done anything

dbcurs.execute("SELECT obsinf.obsind,date_obs,object FROM obsinf LEFT JOIN obscalc ON obsinf.obsind=obscalc.obsind WHERE obscalc.obsind IS NULL AND ind!=0")
rows = dbcurs.fetchall()
todo = len(rows)

if todo == 0:
    print("No new rows the calculate moon phase for", file=sys.stderr)
else:
    perc = 100.0 / todo
    nreached = 0

    for obsind, date, obj in rows:

        nreached += 1
        if count != 0 and nreached % count == 0:
            print("%sReached %d of %d %.2f%%" % (descr, nreached, todo, nreached * perc), file=sys.stderr)
        targname = get_target(obj)
        if targname is None:
            continue
        visible, moonphase, sep = get_moonpars(targname, date)
        dbcurs.execute("INSERT INTO obscalc (obsind,moonvis,moonphase,moondist) VALUES (%d,%d,%.6g,%.6g)" % (obsind, visible, moonphase, sep))
        dbase.commit()

# Repeat that for where we've got sky level but not moon phase

dbcurs.execute("SELECT obsinf.obsind,date_obs,object FROM obsinf INNER JOIN obscalc ON obsinf.obsind=obscalc.obsind WHERE obscalc.moonphase IS NULL AND ind!=0")
rows = dbcurs.fetchall()
todo = len(rows)

if todo == 0:
    print("No existing rows the calculate moon phase for", file=sys.stderr)
else:
    perc = 100.0 / todo
    nreached = 0

    for obsind, date, obj in rows:

        nreached += 1
        if count != 0 and nreached % count == 0:
            print("%sReached update %d of %d %.2f%%" % (descr, nreached, todo, nreached * perc), file=sys.stderr)
        targname = get_target(obj)
        if targname is None:
            continue
        visible, moonphase, sep = get_moonpars(targname, date)
        dbcurs.execute("UPDATE obscalc SET moonvis=%d,moonphase=%.6g,moondist=%.6g WHERE obsind=%d" % (visible, moonphase, sep, obsind))
        dbase.commit()
