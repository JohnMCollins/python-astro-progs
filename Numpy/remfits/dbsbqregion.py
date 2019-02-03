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
import dbops
import dbobjinfo
import sys
import math
import re
from numpy.ma.core import is_mask
from pygments.lexers.grammar_notation import AbnfLexer

def is_masked(num):
    """Return is number is masked"""
    return num is None or type(num) is np.ma.core.MaskedConstant

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)
autils.suppress_vo_warnings()

parsearg = argparse.ArgumentParser(description='List objects close to given object from Simbad', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('object', nargs=1, type=str, help='Object name to specify region for')
parsearg.add_argument('--database', type=str, default='remfits', help='File to use for database')
parsearg.add_argument('--radius', type=int, default=2, help='Radius in arc,om')
parsearg.add_argument('--maxmag', type=float, default=25.0, help='Maximum magnitude to accept')

resargs = vars(parsearg.parse_args())

objname = resargs['object'][0]
dbname = resargs['database']
radius = resargs['radius']
maxmag = resargs['maxmag']

try:
    dbase = dbops.opendb(dbname)
except dbops.dbopsError as e:
    print("Could not open database", dbname, "Error was", e.args[0], file=sys.stderr)
    sys.exit(10)

mycursor = dbase.cursor()

try:
    objname = dbobjinfo.get_targetname(mycursor, objname)
    objd = dbobjinfo.get_object(mycursor, objname)
except dbobjinfo.ObjDataError as e:
    print("Error with object", objname, ":", e.args[0], file=sys.stderr)
    sys.exit(31)

lookupnames = dict()
for n in objd.get_names(mycursor):
    lookupnames[n] = 1

multsp = re.compile(" {2,}")
marks = re.compile("b'(.*)'")

sb = Simbad()
sb.add_votable_fields('main_id', 'id', 'otype', 'dec','distance','pmra','pmdec', 'rv_value')
for f in 'urigzHJK':
    sb.add_votable_fields('flux(' + f + ')', 'flux_error(' + f + ')')

qres = sb.query_region(objname, radius=radius * u.arcmin)
if qres is None:
    print("Cannot find", name, "in Simbad", file=sys.stderr)
    sys.exit(50)

namesadded = []

for qr in qres:
    name = multsp.sub(" ", marks.sub(lambda m: m.group(1), str(qr['MAIN_ID'])))
    if name in lookupnames:
        continue
    lookupnames[name] = 1
    
    otype = qr['OTYPE']
    rvel = None
    try:
        rvel = qr['RV_VALUE']
        if  math.isnan(rvel):
            rvel = None
    except KeyError:
        pass
    try:
        distunit = qr['Distance_unit']
    except KeyError:
        distunit = 'pc'
    try:
        distance = qr['Distance_distance']
        if is_masked(distance):
            distance = None
        elif distunit != 'pc':
            distance = u.Quantity(distance, unit=distunit).to('pc').value
    except KeyError:
        distance = None
    
    nobj = dbobjinfo.ObjData(objname = name, objtype = otype, dist = distance, rv = rvel)
    
    ra = qr['RA']
    dec = qr['DEC']
    sk = coordinates.SkyCoord(ra=ra, dec=dec, unit=(u.hour, u.deg))
    ra = sk.ra.deg
    dec = sk.dec.deg
    pmra = qr['PMRA']
    pmdec = qr['PMDEC']
    if is_masked(pmra):
        pmra = None
    if is_masked(pmdec):
        pmdec = None
    raerr = qr['RA_PREC']
    decerr = qr['DEC_PREC']
    if is_masked(raerr):
        raerr = None
    if is_mask(decerr):
        decerr = None
        
    nobj.set_ra(value=ra, err=raerr, pm=pmra)
    nobj.set_dec(value=dec, err=decerr, pm=pmdec)
    for f in 'urigzHJK':
        flux = qr['FLUX_' + f]
        fluxerr = qr['FLUX_ERROR_' + f]
        if is_masked(flux):
            continue
        if is_masked(fluxerr):
            fluxerr = None
        nobj.set_mag(f, flux, fluxerr)
    
    if nobj.get_maxmag() > maxmag:
        continue
    
    nobj.add_object(mycursor)
    namesadded.append(name)

dbase.commit()
namesadded.sort()
print(len(namesadded), "objects added")
for p in namesadded:
    print(p)

