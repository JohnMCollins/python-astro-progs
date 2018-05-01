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
except objinfo.ObjInfoError:
    pass

if delete:
    errors = 0
    edict = dict()
    for name in objnames:
        try:
            nobj = objinfo.getname(name)
            edict[nobj.objname] = 1
        except objinfo.ObjInfoError as e:
            print e.args[0] >>sys.stderr
            errors += 1
    if errors > 0:
        print "Aborting due to errors" >>sys.stderr
        sys.exit(10)
    for n in edict:
        objinfo.del_object(n)
    objinf.savefile(libfile)
    sys.exit(0)


            


