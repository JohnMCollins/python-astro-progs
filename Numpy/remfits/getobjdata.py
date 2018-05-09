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
parsearg.add_argument('--libfile', type=str, default='~/lib/stellar_data', help='File to use for database')
parsearg.add_argument('--update', action='store_true', help='Update existing names')
parsearg.add_argument('--delete', action='store_true', help='Delete names')

resargs = vars(parsearg.parse_args())

objnames = resargs['objects']
libfile = os.path.expanduser(resargs['libfile'])
update = resargs['update']
delete = resargs['delete']

if update and delete:
    print "Cannot have update and delete options at once" >>sys.stderr

objinf = objinfo.ObjInfo()
try:
    objinf.loadfile(libfile)
except objinfo.ObjInfoError as e:
    if e.warningonly:
        print >>sys.stderr, "(Warning) file does not exist:", libfile
    else:
        print >>sys.stderr, "Error loading file", e.args[0]
        sys.exit(30)

errors = 0
edict = dict()

if delete: 
    for name in objnames:
        try:
            nobj = objinf.get_object(name)
            objinf.del_object(nobj)
        except objinfo.ObjInfoError as e:
            print  >>sys.stderr, e.args[0]
            errors += 1
    if errors > 0:
        print  >>sys.stderr, "Aborting due to errors"
        sys.exit(10)
    objinf.savefile(libfile)
    sys.exit(0)

# If updating check all the names given are there
# Otherwise check that they aren't

if update:
    for name in objnames:
        try:
            nobj = objinf.get_object(name)
        except objinfo.ObjInfoError as e:
            print a.args[0] >>sys.stderr
            errors += 1
            continue
        nname = nobj.objname
        if nname in edict:
            if name != nname:
                print  >>sys.stderr, "Already had", name, "aliased to", nname
            else:
                print  >>sys.stderr, "Already had", name
            errors += 1
            continue
        edict[nname] = 1
else:
    for name in objnames:
        if name in edict:
            print  >>sys.stderr, "Already requested addding", name
            errors += 1
            continue
        edict[name] = 1
        try:
            nobj = objinf.get_object(name)
            pname = nobj.objname
            if pname != name:
                print  >>sys.stderr, "Already had", name, "as alias of", pname
            else:
                print  >>sys.stderr, "Already had", name
            errors += 1
            continue
        except objinfo.ObjInfoError:
            pass
            
if errors > 0:
    print  >>sys.stderr, "Aborting due to errors"
    sys.exit(10)

sb = Simbad()
sb.add_votable_fields('main_id','otype','ra','dec','distance','pmra','pmdec', 'rv_value')
for name in objnames:
    qres = sb.query_object(name)
    if qres is None:
        print  >>sys.stderr, "Cannot find", name, "in Simbad"
        continue
    q0 = qres[0]
    qname = q0['MAIN_ID']
    if objinf.is_defined(qname):
        if not update:
            print >>sys.stderr, name, "is already defined as", qname
            errors += 1
            continue
    elif update:
        print >>sys.stderr, name, "is not previously defined"
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
        obj = objinf.get_object(name)
        if qname != obj.sbname:
            if obj.sbname is not None:
                del objinf.sbnames[obj.sbname]
            obj.sbname = qname
            objinf.sbnames[qname] = obj
        obj.set_ra(value=ra, pm = pmra)
        obj.set_dec(vlaue=dec, pm= pmdec)
        if distance is not None:
            obj.dist = distance
    else:
        obj = objinfo.ObjData(objname = name, sbname = qname, objtype = otype, rv = rvel, dist = distance)
        obj.set_ra(value = ra, pm = pmra)
        obj.set_dec(value = dec, pm = pmdec)
        objinf.add_object(obj)

if errors > 0:
    print  >>sys.stderr, "Aborting due to errors"
    sys.exit(20)

objinf.savefile(libfile)
    