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
import parsetime
import dbops

class savedobj(object):
    """Remember details of object for sorting and combining"""

    def __init__(self, id, type, ra, dec, mags, magerrs, ninsts = 1):
        self.id = id
        self.type = type
        self.ra = ra
        self.dec = dec
        self.mags = mags
        self.magerrs = magerrs
        self.ninsts = ninsts
        self.variable = False
        self.obj = None         # if we identify it with an object

class Hadit(Exception):
    """Trhow this to indicate we've had the object"""
    pass

def is_masked(num):
    """Return is number is masked"""
    return num is None or type(num) is np.ma.core.MaskedConstant

def combine(obl):
    """Combine a list of objects into one"""

    if len(obl) == 1:
        return obl[0]
    cra = [x.ra for x in obl]
    cdec = [x.dec for x in obl]
    cmags = dict()
    cmagerrs = dict()
    ov = False
    for f in "urigzHJK":
        magl = [x.mags[f] for x in obl]
        magerrl = [x.magerrs[f] for x in obl]
        cmags[f] = np.mean(magl)
        comberr = math.sqrt(np.mean(np.array(magerrl) ** 2))
        s = np.std(magl)
        if s > comberr:
            print("Object %d at (%.3f,%.3f) overlarge variation filter %s combined %.3f actual %.3f" % (obl[0].id, np.mean(cra), np.mean(cdec), f, comberr, s), file=sys.stderr)
            ov = True
            comberr = s
        cmagerrs[f] = comberr
    r = savedobj(obl[0].id, obl[0].type, np.mean(cra), np.mean(cdec), cmags, cmagerrs, len(obl))
    r.variable = ov
    return r

parsearg = argparse.ArgumentParser(description='List objects close to given object from SDSS', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('object', nargs=1, type=str, help='Object name to specify region for')
parsearg.add_argument('--database', type=str, default='remfits', help='Database to use')
parsearg.add_argument('--radius', type=float, default=10, help='Radius in arcminutes')
parsearg.add_argument('--samerad', type=float, default=1, help='Treat objects as same if in this number of arcminutes')
parsearg.add_argument('--maxmag', type=float, default=15.0, help='Maximum magnitude to accept')
parsearg.add_argument('--onlytype', type=int, help='Only accept this type code from SDSS DB 3=galaxy 6=star')
parsearg.add_argument('--insert', action='store_true', help='Add records to database')
parsearg.add_argument('--force', action='store_true', help='Force update of magnitudes')
parsearg.add_argument('--basetime', type=str, help='Time/date for proper motions default today')

resargs = vars(parsearg.parse_args())

objname = resargs['object'][0]
dbname = resargs['database']
radius = resargs['radius'] / 60.0
samerad = resargs['samerad'] / 60.0
maxmag = resargs['maxmag']
addobjs = resargs['insert']
basetime = resargs['basetime']
onlytype = resargs['onlytype']
force = resargs['force']

if basetime is None:
    basetime = datetime.datetime.now()
else:
    try:
        basetime = parsetime.parsetime(basetime)
    except ValueError:
        print("Do not understand date", basetime, file=sys.stderr)
        sys.exit(20)

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

# Get position of object for 2000 time and and given time

RA2000 = objd.get_ra()
DEC2000 = objd.get_dec()
RACurr = objd.get_ra(basetime)
DECCurr = objd.get_dec(basetime)

Objcoord = coordinates.SkyCoord(ra = RACurr, dec = DECCurr, unit=u.deg)

fields = ['objID','type', 'ra','dec']
for l in 'urigzHJK':
    fields.append(l)
    fields.append('Err_' + l)

Sdobjs = SDSS.query_region(Objcoord, photoobj_fields=fields,radius=radius*u.deg)

if Sdobjs is None:
    print("No objects found in region of", objname, file=sys.stderr)
    sys.exit(1)

# Convert to temp type for fiddling with eliminating too faint objs and ones with no mags

convsdobjs = []
for r in Sdobjs:
    if onlytype is not None and r['type'] != onlytype:
        continue
    maglist = []
    for i in 'urigz':
        maglist.append(r[i])
    mm = np.min(maglist)
    if mm < 0 or np.min(maglist) > maxmag:
        continue
    dm = dict()
    de = dict()
    for f in 'urigz':
        dm[f] = r[f]
        de[f] = r['Err_' + f]
    convsdobjs.append(savedobj(r['objID'], r['type'], r['ra'], r['dec'], dm, de))

# Sort into order by object type and ra/dec

convsdobjs.sort(key=lambda x: (x.type, x.ra, x.dec))
print("Number of objects prior to combination =", len(convsdobjs))

#for r in convsdobjs:
#    print("%d %.4f %.4f %d %.3f %.3f %.3f %.3f %.3f %.3f %.3f %.3f" % \
#        (r.id, r.ra, r.dec, r.type, r.mags['g'], r.mags['i'], r.mags['r'], r.mags['z'], \
#         r.magerrs['g'], r.magerrs['i'], r.magerrs['r'], r.magerrs['z']))

# This is where we merge together 2 or more obs of the same thing

diffrad2 = samerad ** 2
combined = []
subs = []
curr = convsdobjs.pop(0)
try:
    while 1:
        subs = [ curr ]
        while 1:
            next = convsdobjs.pop(0)
            if next.type != curr.type or (next.ra - curr.ra) ** 2 + (next.dec - curr.dec) ** 2 > diffrad2:
                break
            subs.append(next)
        combined.append(combine(subs))
        curr = next
except IndexError:
    if len(subs) != 0:
        combined.append(combine(subs))

print("Number of objects after combination = ", len(combined))

for r in combined:
    s = ""
    obn = ""
    if r.variable: s = "(var)"
    #print("%d %.4f %.4f %d %.3f %.3f %.3f %.3f %.3f %.3f %.3f %.3f (%d) %s" % \
     #    (r.id, r.ra, r.dec, r.type, r.mags['g'], r.mags['i'], r.mags['r'], r.mags['z'], \
     #    r.magerrs['g'], r.magerrs['i'], r.magerrs['r'], r.magerrs['z'], r.ninsts, s))

libobj_curr = dbobjinfo.get_objlist(mycursor, RACurr, DECCurr, samerad, basetime)

for p in combined:
    for ra, dec, obj in libobj_curr:
        if (ra - p.ra)**2 + (dec - p.dec)**2 <= diffrad2:
            if p.obj is not None:
                print("Same match radius too large clashing with", p.obj.objname, "and", obj.objname, file=sys.stderr)
                sys.exit(2)
            p.obj = obj
            print("identified object type %d at (%.4f,%.4f)" % (p.type, p.ra, p.dec), "as", p.obj.objname)
            break

if not addobjs:
    sys.exit(0)

for p in combined:
    obj = p.obj
    if obj is None:
        objname = "SDSS" + str(p.id)
        objtype = "star"
        if p.type == 3: objtype = "galaxy"
        obj = dbobjinfo.ObjData(objname = objname, objtype = objtype, ra = p.ra, dec = p.dec)
    dbobjinfo.add_alias(mycursor, objname, str(p.id), "SDSS")
    for f in 'urigzHJK':
        obj.set_mag(filter = f, value = p.mags[f], err = p.magerrs[f], force = force)
    if p.obj is None:
        obj.add_object(mycursor)
    else:
        obj.update_filters(mycursor)

dbase.commit()