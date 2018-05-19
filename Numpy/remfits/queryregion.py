#!  /usr/bin/env python

# Get object data and maintain XML Database

from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
from astroquery.simbad import Simbad
from astropy import coordinates
from astropy.time import Time
import datetime
import astropy.units as u
import astroquery.utils as autils
import numpy as np
import os.path
import argparse
import warnings
import xmlutil
import objinfo
import sys
import math

def is_masked(num):
    """Return is number is masked"""
    return type(num) is np.ma.core.MaskedConstant

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)
autils.suppress_vo_warnings()

parsearg = argparse.ArgumentParser(description='List objects close to given object', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('object', nargs=1, type=str, help='Object name to specify region for')
parsearg.add_argument('--libfile', type=str, default='~/lib/stellar_data', help='File to use for database')
parsearg.add_argument('--radius', type=int, default=2, help='Radius in arc,om')
parsearg.add_argument('--filter', type=str, default='V', help='filter for flux')
parsearg.add_argument('--maxmag', type=float, default=15.0, help='Maximum magnitude to accept')
parsearg.add_argument('--insert', action='store_true', help='Add records to database')

resargs = vars(parsearg.parse_args())

objname = resargs['object'][0]
libfile = os.path.expanduser(resargs['libfile'])
radius = resargs['radius']
filter = resargs['filter']
maxmag = resargs['maxmag']
addobjs = resargs['insert']

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
    objd = objinf.get_object(objname)
except objinfo.ObjInfoError as e:
    print >>sys.stderr, "Error with object", objname, ":", e.args[0]
    sys.exit(31)

lookupname = objd.sbname
if lookupname is None:
    lookupname = objd.objname

sb = Simbad()
sb.add_votable_fields('main_id','otype','ra','dec','distance','pmra','pmdec', 'rv_value', 'fluxdata(' + filter + ')')
qres = sb.query_region(lookupname, radius=radius * u.arcmin)
if qres is None:
    print  >>sys.stderr, "Cannot find", name, "in Simbad"
    sys.exit(50)

results = []
lengths = [0,0,0,0,0]
for qr in qres:
    flux = qr['FLUX_' + filter]
    if is_masked(flux) or flux > maxmag:
        continue
    name = qr['MAIN_ID']
    if name == objd.sbname:
        continue
    otype = qr['OTYPE']
    ra = qr['RA']
    dec = qr['DEC']
    sk = coordinates.SkyCoord(ra=ra, dec=dec, unit=(u.hour, u.deg))
    ra = "%.3f" % sk.ra.deg
    dec = "%.3f" % sk.dec.deg
    distance = qr['distance_distance']
    distunit = qr['distance_unit']
    pmra = qr['PMRA']
    pmdec = qr['PMDEC']
    if is_masked(distance):
        distancestr = "-"
        distance = None
    else:
        distancestr = "%#.4g" % u.Quantity(distance, unit=distunit).to('pc').value
        try:
            rvel = qr['RV_VALUE']
            if not math.isnan(rvel):
                distancestr += '*'
        except KeyError:
            distancestr += '*'
    if is_masked(pmra):
        pmra = None
    else:
        ra += '*'
    if is_masked(pmdec):
        pmdec = None
    else:
        dec += '*'
    item = [name, otype, ra, dec, distancestr, flux]
    
    l2 = []
    for ll, ii in zip(lengths, item):
        l2.append(max(ll, len(ii)))
    lengths = l2
    results.append(item)

results.sort(key=lambda y: y[-1])
for res in results:
    for r, l in zip(res, lengths):
        print r + " " * (l - len(r)),
    print "%#.4g" % res[-1]

