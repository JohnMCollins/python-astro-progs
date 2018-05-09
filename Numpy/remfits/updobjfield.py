#!  /usr/bin/env python

# Update object fields

from astropy import coordinates
from astropy.time import Time
import datetime
import astropy.units as u
import astroquery.utils as autils
import numpy as np
import os.path
import argparse
import xmlutil
import objinfo
import sys

parsearg = argparse.ArgumentParser(description='Update object fields', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('object', nargs=1, type=str, help='Object name to process')
parsearg.add_argument('--libfile', type=str, default='~/lib/stellar_data', help='File to use for database')
parsearg.add_argument('--quiet', action='store_true', help='Don not say anything')
parsearg.add_argument('--ra', type=float, help='RA value in degrees')
parsearg.add_argument('--dec', type=float, help='Dec value in degrees')
parsearg.add_argument('--dist', type=float, help='Distance in parsec')
parsearg.add_argument('--pmra', type=float, help='RA propoer motion in mas/year')
parsearg.add_argument('--pmdec', type=float, help='DEC propoer motion in mas/year')
parsearg.add_argument('--rv', type=float, help='Radial velocity in km/s')
parsearg.add_argument('--mag', type=float, help='Magnitude in rel units')
parsearg.add_argument('--sigmag', type=float, help='Magnitude sigma')

resargs = vars(parsearg.parse_args())

objname = resargs['object'][0]
libfile = os.path.expanduser(resargs['libfile'])
quiet = resargs['quiet']
ra = resargs['ra']
dec = resargs['dec']
dist = resargs['dist']
pmra = resargs['pmra']
pmdec = resargs['pmdec']
rv = resargs['rv']
mag = resargs['mag']
sigmag = resargs['sigmag']

objinf = objinfo.ObjInfo()
try:
    objinf.loadfile(libfile)
except objinfo.ObjInfoError as e:
    if e.warningonly:
        print >>sys.stderr, "(Warning) file does not exist:", libfile
    else:
        print >>sys.stderr, "Error loading file", e.args[0]
        sys.exit(30)

try:
    obj = objinf.get_object(objname)
except objinfo.ObjInfoError as e:
    print >>sys.stderr, "Error finding", objname, e.args[0]
    sys.exit(11)

obj.update_ra(value = ra, pm = pmra)
obj.update_dec(value = dec, pm = pmdec)
if dist is not None:
    obj.dist = dist
if rv is not None:
    obj.rv = rv
if mag is not None:
    obj.mag = mag
if sigmag is not None:
    obj.magerr = sigmag
objinf.savefile(libfile)
