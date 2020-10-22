#!  /usr/bin/env python3

# Update object ra/dec/pms/distances

from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
from astroquery.simbad import Simbad
from astropy.coordinates import Angle
from astropy.time import Time
import datetime
import astropy.units as u
import astroquery.utils as autils
import numpy as np
import argparse
import warnings
import dbops
import remdefaults
import sys


def is_masked(num):
    """Return is number is masked"""
    return type(num) is np.ma.core.MaskedConstant

# Shut up warning messages


warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)
autils.suppress_vo_warnings()

parsearg = argparse.ArgumentParser(description='Adjust object ra/dec/pm/dists', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg, libdir=False, tempdir=False)

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)

dbase, mycursor = remdefaults.opendb()

sb = Simbad()
sb.add_votable_fields('pm', 'distance', 'rv_value')

mycursor.execute("SELECT objname FROM objdata")

objlist = mycursor.fetchall()

for obj, in objlist:
    sbd = sb.query_object(obj)
    if sbd is None:
        print("Could not find", obj)
        continue
    updates = []
    sbr = sbd[0]
    ra = Angle(sbr['RA'], unit=u.hour).deg
    updates.append("radeg=%.8e" % ra)
    rae = sbr['RA_PREC']
    updates.append("raerr=%.8e" % rae)
    rapm = sbr['PMRA']
    if not is_masked(rapm):
        updates.append("rapm=%.8e" % rapm)
    dec = Angle(sbr['DEC'], unit=u.deg).deg
    updates.append("decdeg=%.8e" % dec)
    dece = sbr['DEC_PREC']
    updates.append("decerr=%.8e" % dece)
    decpm = sbr['PMDEC']
    if not is_masked(decpm):
        updates.append("decpm=%.8e" % decpm)
    dist = sbr['Distance_distance']
    distu = sbr['Distance_unit']
    if not is_masked(dist) and not is_masked(distu):
        dist = u.Quantity(dist, unit=distu).to(u.pc).value
        updates.append('dist=%.8e' % dist)
    rvel = sbr['RV_VALUE']
    if not is_masked(rvel):
        updates.append("rv=%.8e" % rvel)
    updates = ",".join(updates)
    mycursor.execute("UPDATE objdata SET " + updates + " WHERE objname=" + dbase.escape(obj))

dbase.commit()
