#!  /usr/bin/env python3

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
import dbops
import dbobjinfo
import sys
from dbops import dbopsError

def is_masked(num):
    """Return is number is masked"""
    return type(num) is np.ma.core.MaskedConstant

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)
autils.suppress_vo_warnings()

parsearg = argparse.ArgumentParser(description='Get object info into database', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('objects', nargs='+', type=str, help='Object names to process')
parsearg.add_argument('--database', type=str, default='remfits', help='Database to use')
parsearg.add_argument('--update', action='store_true', help='Update existing names')
parsearg.add_argument('--delete', action='store_true', help='Delete names')

resargs = vars(parsearg.parse_args())

objnames = resargs['objects']
dbname = os.path.expanduser(resargs['database'])
update = resargs['update']
delete = resargs['delete']

if update and delete:
    print("Cannot have update and delete options at once" >>sys.stderr)

try:
    dbase = dbops.opendb(dbname)
except dbops.dbopsError as e:
    print("Could not open database", dbname, "Error was", e.args[0])
    sys.exit(10)

mycursor = dbase.cursor()

errors = 0
edict = dict()

if delete:
    for name in objnames:
        try:
            nobj = dbobjinfo.get_object(mycursor, name)
            dbobjinfo.del_object(nobj)
        except dbobjinfo.ObjDataError as e:
            print(e.args[0], file=sys.stderr)
            errors += 1
    if errors > 0:
        print("Aborting due to errors", file=sys.stderr)
        sys.exit(10)
    sys.exit(0)

# If updating check all the names given are there
# Otherwise check that they aren't

if update:
    for name in objnames:
        try:
            nobj = dbobjinfo.get_object(mycursor, name)
        except dbobjinfo.ObjDataError as e:
            print(a.args[0], file=sys.stderr)
            errors += 1
            continue
        nname = nobj.objname
        if nname in edict:
            if name != nname:
                print("Already had", name, "aliased to", nname, file=sys.stderr)
            else:
                print("Already had", name, file=sys.stderr)
            errors += 1
            continue
        edict[nname] = 1
else:
    for name in objnames:
        if name in edict:
            print("Already requested addding", name, file=sys.stderr)
            errors += 1
            continue
        edict[name] = 1
        try:
            nobj = dbobjinfo.get_object(mycursor, name)
            pname = nobj.objname
            if pname != name:
                print("Already had", name, "as alias of", pname, file=sys.stderr)
            else:
                print("Already had", name, file=sys.stderr)
            errors += 1
            continue
        except dbobjinfo.ObjInfoError:
            pass

if errors > 0:
    print("Aborting due to errors", file=sys.stderr)
    sys.exit(10)

sb = Simbad()
sb.add_votable_fields('main_id','otype','ra','dec','distance','pmra','pmdec', 'rv_value')
for name in objnames:
    qres = sb.query_object(name)
    if qres is None:
        print("Cannot find", name, "in Simbad", file=sys.stderr)
        continue
    q0 = qres[0]
    qname = q0['MAIN_ID']
    if objinf.is_defined(qname):
        if not update:
            print(name, "is already defined as", qname, file=sys.stderr)
            errors += 1
            continue
    elif update:
        print(name, "is not previously defined", file=sys.stderr)
        errors += 1
        continue

    otype = q0['OTYPE']
    ra = coordinates.Angle(q0['RA'], unit=u.hour).deg
    dec = coordinates.Angle(q0['DEC'], unit=u.deg).deg
    distance = q0['distance_distance']
    distunit = q0['distance_unit']
    pmra = q0['PMRA']
    pmdec = q0['PMDEC']
    try:
        rvel = q0['RV_VALUE']
    except KeyError:
        rvel = None
    if is_masked(distance):
        distance = None
    else:
        distance = u.Quantity(distance, unit=distunit).to('pc').value
    if is_masked(pmra):
        pmra = None
    if is_masked(pmdec):
        pmdec = None
    if update:
        obj = dbobjinfo.get_object(mycursor, name)
        obj.set_ra(value=ra, pm = pmra)
        obj.set_dec(vlaue=dec, pm= pmdec)
        if distance is not None:
            obj.dist = distance
    else:
        obj = dbobjinfo.ObjData(objname = name, objtype = otype, rv = rvel, dist = distance)
        obj.set_ra(value = ra, pm = pmra)
        obj.set_dec(value = dec, pm = pmdec)
        if qname != name:
            obj.set_alias(qname, 'Simbad')
        objinf.add_object(obj)

if errors > 0:
    print("Aborting due to errors", file=sys.stderr)
    sys.exit(20)
