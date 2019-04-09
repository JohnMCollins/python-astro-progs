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
import remdefaults
import dbobjinfo
import sys
from dbops import dbopsError
from imageio.plugins._tifffile import asbool

def is_masked(num):
    """Return is number is masked"""
    return type(num) is np.ma.core.MaskedConstant

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)
autils.suppress_vo_warnings()

parsearg = argparse.ArgumentParser(description='Get fluxes of objects in Simbad', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('--database', type=str, default=remdefaults.default_database(), help='Database to use')
parsearg.add_argument('--force', action='store_true', help='Force override of existing')
parsearg.add_argument('--verbose', action='store_true', help='Give messages of what  happens')

resargs = vars(parsearg.parse_args())
verbose = resargs['verbose']
force = resargs['force']
dbname = os.path.expanduser(resargs['database'])

try:
    dbase = dbops.opendb(dbname)
except dbops.dbopsError as e:
    print("Could not open database", dbname, "Error was", e.args[0], file=sys.stderr)
    sys.exit(10)

mycursor = dbase.cursor()

if  mycursor.execute("SELECT " + dbobjinfo.Objdata_fields + " FROM objdata") == 0:
    print("Could not find any objects in database", file=sys.stderr)
    sys.exit(11)

objtab = mycursor.fetchall()

sb = Simbad()

for f in 'urigzHJK':
    sb.add_votable_fields('flux(' + f + ')', 'flux_error(' + f + ')')

for objt in objtab:
    cobj = dbobjinfo.ObjData()
    cobj.load_dbrow(objt)
    if cobj.objname[0:4] == 'SDSS':
        continue
    sbdets = sb.query_object(cobj.objname)
    if sbdets is None:
        if verbose:
            print(cobj.objname, "not found in Simbad", file=sys.stderr)
        continue
    sbdets = sbdets[0]
    changes = 0
    for f in 'urigzHJK':
        val = sbdets['FLUX_' + f]
        if not is_masked(val):
            err = sbdets['FLUX_ERROR_' + f]
            if is_masked(err):
                err = None
            if cobj.set_mag(f, val, err, force):
                changes += 1
    if  changes > 0:
        cobj.update_filters(mycursor)
        dbase.commit()
        if verbose:
            print("Updated", changes, "filters on", cobj.objname, file=sys.stderr)
 
