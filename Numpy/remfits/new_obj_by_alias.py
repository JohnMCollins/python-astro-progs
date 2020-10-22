#!  /usr/bin/env python3

from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
from astroquery.simbad import Simbad
from astropy import coordinates
from astropy.time import Time
import datetime
import astropy.units as u
import astroquery.utils as autils
import numpy as np
import argparse
import warnings
import dbops
import remdefaults
import dbobjinfo
import sys
import re

multispace = re.compile("\s\s+")


def is_masked(num):
    """Return is number is masked"""
    return type(num) is np.ma.core.MaskedConstant


class NameClash(Exception):
    """Throw this if name clashes"""
    pass


def name_used(mycursor, name):
    """Check if name is a name or alias of something we've got"""
    try:
        nobj = dbobjinfo.get_object(mycursor, name)
        pname = nobj.objname
        if pname != name:
            raise NameClash("Already had " + name + " as an alias of " + pname)
        raise NameClash("Already had object " + name)
    except dbobjinfo.ObjDataError:
        pass

# Shut up warning messages


warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)
autils.suppress_vo_warnings()

parsearg = argparse.ArgumentParser(description='Insert object info given name, ra, dec', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg, libdir=False, tempdir=False)
parsearg.add_argument('args', nargs=3, type=str, help='Object name, ra and dec as strings')
parsearg.add_argument('--radius', type=float, default=20.0, help='Radius to search in arcmin')
parsearg.add_argument('--select', type=int, help='Item to select otherwise just list')

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
name, ra, dec = resargs['args']
radius = resargs['radius']
select = resargs['select']

dbase, mycursor = remdefaults.opendb()
try:
    name_used(mycursor, name)
except  NameClash as e:
    print(e.args[0], file=sys.stderr)
    sys.exit(10)

sb = Simbad()
sb.add_votable_fields('main_id', 'id', 'otype', 'ra', 'dec', 'distance', 'pmra', 'pmdec', 'rv_value')
sk = coordinates.SkyCoord(ra=coordinates.Angle(ra, unit=u.hour), dec=coordinates.Angle(dec, unit=u.deg))

rt = sb.query_region(sk, radius=radius * u.arcmin)
if rt is None:
    print("Nothing found in region of", ra, dec, "for", name)
    sys.exit(1)

n = 0

for res in rt:
    mainid = multispace.sub(" ", res['MAIN_ID'].decode())
    otherids = res['ID'].decode()
    otype = res['OTYPE'].decode()
    ra = coordinates.Angle(res['RA'], unit=u.hour)
    dec = coordinates.Angle(res['DEC'], unit=u.deg)
    skr = coordinates.SkyCoord(ra=ra, dec=dec)
    sep = sk.separation(skr).deg
    msg = ""
    try:
        name_used(mycursor, mainid)
    except NameClash as e:
        msg = e.args[0]
    otherid_aliases = set([multispace.sub(" ", t.strip()) for t in otherids.split(',')])
    nosp_aliases = set([t.replace(" ", "") for t in otherid_aliases])
    nosp_main = mainid.replace(" ", "")
    otherid_aliases |= nosp_aliases
    if nosp_main != mainid:
        otherid_aliases.add(nosp_main)
    for a in otherid_aliases:
        try:
            name_used(mycursor, a)
        except NameClash as e:
            if len(msg) != 0:
                msg += ','
            msg += e.args[0]
    print("%-20s %-10s %12.6f %12.6f %12.6f %s" % (mainid, otype, ra.deg, dec.deg, sep, msg))
    for a in sorted(list(otherid_aliases)):
        print("\t", a, sep='')

    if select is not None and select == n:
        if len(msg) != 0:
            print("Not adding this as probable errors", file=sys.stderr)
            sys.exit(2)
        distance = res['Distance_distance']
        distunit = res['Distance_unit']
        pmra = res['PMRA']
        pmdec = res['PMDEC']
        try:
            rvel = res['RV_VALUE']
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
        obj = dbobjinfo.ObjData(objname=mainid, objtype=otype, rv=rvel, dist=distance)
        obj.set_ra(value=ra.deg, pm=pmra)
        obj.set_dec(value=dec.deg, pm=pmdec)
        obj.add_object(mycursor)
        otherid_aliases.add(name)
        for a in otherid_aliases:
            dbobjinfo.add_alias(mycursor, mainid, a, 'Simbad region query')
        dbase.commit()
        sys.exit(0)
    n += 1
