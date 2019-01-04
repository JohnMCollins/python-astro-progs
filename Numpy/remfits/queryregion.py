#!  /usr/bin/env python3

# @Author: John M Collins <jmc>
# @Date:   2019-01-04T22:45:59+00:00
# @Email:  jmc@toad.me.uk
# @Filename: queryregion.py
# @Last modified by:   jmc
# @Last modified time: 2019-01-04T23:16:06+00:00

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
    return num is None or type(num) is np.ma.core.MaskedConstant

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
        print("(Warning) file does not exist:", libfile, file=sys.stderr)
    else:
        print("Error loading file", e.args[0], file=sys.stderr)
        sys.exit(30)

try:
    objd = objinf.get_object(objname)
except objinfo.ObjInfoError as e:
    print("Error with object", objname, ":", e.args[0], file=sys.stderr)
    sys.exit(31)

als = objd.list_aliases()
lookupname = None
for al in als:
    if al.source == "Simbad":
        LookupError = al.objname
        break
if lookupname is None:
    lookupname = objd.objname

sb = Simbad()
sb.add_votable_fields('main_id','otype','ra','dec','distance','pmra','pmdec', 'rv_value', 'fluxdata(' + filter + ')')
qres = sb.query_region(lookupname, radius=radius * u.arcmin)
if qres is None:
    print("Cannot find", name, "in Simbad", file=sys.stderr)
    sys.exit(50)

results = []
namesadded = []
lengths = [0,0,0,0,0]
for qr in qres:
    flux = qr['FLUX_' + filter]
    if is_masked(flux) or flux > maxmag:
        continue
    name = qr['MAIN_ID']
    if name == lookupname:
        continue
    otype = qr['OTYPE']
    ra = qr['RA']
    dec = qr['DEC']
    sk = coordinates.SkyCoord(ra=ra, dec=dec, unit=(u.hour, u.deg))
    ra = sk.ra.deg
    dec = sk.dec.deg
    rastr = "%.3f" % ra
    decstr = "%.3f" % dec
    try:
        distance = qr['distance_distance']
    except KeyError:
        distance = None
    try:
        distunit = qr['distance_unit']
    except KeyError:
        distunit = None
    pmra = qr['PMRA']
    pmdec = qr['PMDEC']
    rvel = None
    if is_masked(distance):
        distancestr = "-"
        distance = None
    else:
        distancestr = "%#.4g" % u.Quantity(distance, unit=distunit).to('pc').value
        try:
            rvel = qr['RV_VALUE']
            if  math.isnan(rvel):
                rvel = None
            else:
                distancestr += '*'
        except KeyError:
            distancestr += '*'
    if is_masked(pmra):
        pmra = None
    else:
        rastr += '*'
    if is_masked(pmdec):
        pmdec = None
    else:
        decstr += '*'
    item = [name, otype, rastr, decstr, distancestr, flux]

    l2 = []
    for ll, ii in zip(lengths, item):
        l2.append(max(ll, len(ii)))
    lengths = l2
    results.append(item)
    if addobjs and not objinf.is_defined(name):
        myname = name.translate(None, " ")
        newobj = objinfo.ObjData(objname = myname, objtype = otype, dist = distance, rv = None)
        newobj.set_alias(name, 'Simbad')
        newobj.set_ra(value = ra, pm = pmra)
        newobj.set_dec(value = dec, pm = pmdec)
        objinf.add_object(newobj)
        namesadded.append(myname)

namesadded.sort()
for n in namesadded:
    print("Added", n)

results.sort(key=lambda y: y[-1])
for res in results:
    for r, l in zip(res, lengths):
        print(r + " " * (l - len(r)), end=' ')
    print("%#.4g" % res[-1])

if len(namesadded) != 0:
    objinf.savefile()
    print("Saved new file")
