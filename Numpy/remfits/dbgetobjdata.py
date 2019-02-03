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
parsearg.add_argument('--delete', action='store_true', help='Delete names')

resargs = vars(parsearg.parse_args())

objnames = resargs['objects']
dbname = os.path.expanduser(resargs['database'])
delete = resargs['delete']

try:
    dbase = dbops.opendb(dbname)
except dbops.dbopsError as e:
    print("Could not open database", dbname, "Error was", e.args[0], file=sys.stderr)
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
    except dbobjinfo.ObjDataError:
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
        errors += 1
        continue
    q0 = qres[0]
    qname = q0['MAIN_ID']
    if dbobjinfo.is_defined(mycursor, str(qname)):
        print(name, "is already defined as", qname, file=sys.stderr)
        errors += 1
        continue

    otype = q0['OTYPE']
    ra = coordinates.Angle(q0['RA'], unit=u.hour).deg
    dec = coordinates.Angle(q0['DEC'], unit=u.deg).deg
    distance = q0['Distance_distance']
    distunit = q0['Distance_unit']
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
    obj = dbobjinfo.ObjData(objname = name, objtype = otype, rv = rvel, dist = distance)
    obj.set_ra(value = ra, pm = pmra)
    obj.set_dec(value = dec, pm = pmdec)
    try:
        if qname != name:
            dbobjinfo.add_alias(mycursor, name, qname, 'Simbad')
        obj.add_object(mycursor)
    except dbobjinfo.ObjDataError as e:
        print("Problems adding", name, "error was", e.args[0])
        errors += 1

if errors > 0:
    print("Erors on", errors, "file(s)", file=sys.stderr)
    dbase.commit()
    sys.exit(20)

dbase.commit()
