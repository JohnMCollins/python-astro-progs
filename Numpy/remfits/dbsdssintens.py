#!  /usr/bin/env python3

# @Author: John M Collins <jmc>
# @Date:   2019-01-04T22:45:59+00:00
# @Email:  jmc@toad.me.uk
# @Filename: sdssqregion.py
# @Last modified by:   jmc
# @Last modified time: 2019-01-04T23:17:43+00:00

# Get object data and maintain XML Database

from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
from astropy import coordinates
from astropy.time import Time
import datetime
import astropy.units as u
import astroquery.utils as autils
import numpy as np
import os.path
import argparse
import warnings
warnings.filterwarnings('ignore')
from astroquery.sdss import SDSS
import dbobjinfo
import sys
import math
import dbops
import remdefaults

parsearg = argparse.ArgumentParser(description='Reset intensities of SDSS objects', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('--database', type=str, default=remdefaults.default_database(), help='Database to use')
parsearg.add_argument('--radius', type=float, default=2, help='Radius in arcminutes')
parsearg.add_argument('--samerad', type=float, default=1, help='Treat objects as same if in this number of arcminutes')

resargs = vars(parsearg.parse_args())

dbname = resargs['database']
radius = resargs['radius'] / 60.0
samerad = resargs['samerad'] / 60.0

try:
    dbase = dbops.opendb(dbname)
except dbops.dbopsError as e:
    print("Could not open database", dbname, "Error was", e.args[0], file=sys.stderr)
    sys.exit(10)

mycursor = dbase.cursor()

mycursor.execute("SELECT " + dbobjinfo.Objdata_fields + " FROM objdata WHERE objname REGEXP 'SDSS.*'")

sdsstab = mycursor.fetchall()

fields = ['objID','type', 'ra','dec']
for l in 'urigzHJK':
    fields.append(l)
    fields.append('Err_' + l)

for sdssitem in sdsstab:
    sdssobj = dbobjinfo.ObjData()
    sdssobj.load_dbrow(sdssitem)
    Objcoord = coordinates.SkyCoord(ra = sdssobj.rightasc.value, dec = sdssobj.decl.value, unit=u.deg)
    print(Objcoord, fields, sep='\n', file=sys.stdout)
    Sdobjs = SDSS.query_region(Objcoord, photoobj_fields=fields,radius=radius*u.deg)
    if Sdobjs is None:
        print("No objects found in region of", sdssobj.objname, file=sys.stderr)
        continue
    objid = int(sdssobj.objname[4:])
    for sob in Sdobjs:
        if sob['objID'] == objid:
            for f in 'urigzHJK':
                sdssobj.set_mag(filter = f, value = sob[f], err = sob['Err_' + f])
            sdssobj.update_filters(mycursor)
            break

dbase.commit()
