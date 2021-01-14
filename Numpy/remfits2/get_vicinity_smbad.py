#!  /usr/bin/env python3

from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
from astropy.io import fits
from astropy.time import Time
from astroquery.simbad import Simbad
from astropy.coordinates import SkyCoord, Angle
import astropy.units as u
import datetime
import numpy as np
import argparse
import warnings
import sys
import miscutils
import math
import remdefaults
import objdata
import re

multispace = re.compile('\s{2,}')
letspacenum = re.compile('(?<=[a-zA-Z])\s+(?=\d)')
numspacelet = re.compile('(?<=\d)\s+(?=[a-zA-Z])')
namepref = re.compile('NAME\s+')


def stripit(name):
    """Strip spaces etc off name"""
    return namepref.sub("", letspacenum.sub("", numspacelet.sub("", multispace.sub(" ", name.strip()))))


def parse_aliases(value):
    """Return a list of aliases as returned by Simbad
     Remove spaces where appropriate"""

    results = []
    for a in value.split('|'):
         a = letspacenum.sub("", numspacelet.sub("", multispace.sub(" ", a.strip())))
         results.append(a)
         results.append(namepref.sub("", a))
    return set(results)


class parse_simbad_result(object):
    """Single result of Simbad search"""

    def __init__(self):
        self.mainname = None
        self.names = None
        self.otype = None
        self.dist = None
        self.rv = None
        self.ra = None
        self.dec = None
        self.rapm = None
        self.decpm = None
        self.fluxes = dict()
        for f in objdata.Possible_filters:
            self.fluxes[f] = None

    def update_object(self, obj):
        """Copy defined fields into object details"""
        obj.objtype = self.otype
        if self.dist is not None:
            obj.dist = self.dist
        if self.rv  is not None:
            obj.rv = self.rv
        if self.ra is not None:
            obj.ra = self.ra
        if self.dec is not None:
            obj.dec = self.dec
        if self.rapm is not None:
            obj.rapm = self.rapm
        if self.decpm is not None:
            obj.decpm = self.decpm
        for f in objdata.Possible_filters:
            val = self.fluxes[f]
            if val is None: continue
            setattr(obj, f + 'mag', val)


def parse_sbresult(sbres):
    """Parse results and return is list of parse_simbad_results"""
    main_ids = [stripit(p) for p in sbres['MAIN_ID'].iter_str_vals()]
    ids = [p for p in sbres['IDS'].iter_str_vals()]
    types = [p for p in sbres['OTYPE'].iter_str_vals()]
    dists = sbres['Distance_distance']
    distus = sbres['Distance_unit']
    rvs = sbres['RV_VALUE']
    ras = sbres['RA']
    decs = sbres['DEC']
    rapms = sbres['PMRA']
    decpms = sbres['PMDEC']
    fluxes = dict()
    for f in objdata.Possible_filters:
        if f != 'z':
            fluxes[f] = sbres['FLUX_' + f.upper()]

    result = []
    for obj in range(0, len(main_ids)):
        p = parse_simbad_result()
        p.mainname = main_ids[obj]  # In case we need it
        p.names = parse_aliases(main_ids[obj]) | parse_aliases(ids[obj])
        p.otype = types[obj]
        if p.otype.lower().startswith('planet') or p.otype.upper().startswith('IR'):
            continue
        dist = float(dists[obj])
        if not math.isnan(dist):
            p.dist = u.Quantity(dist, unit=distus[obj]).to_value(u.lightyear)
        rv = float(rvs[obj])
        if not math.isnan(rv):
            p.rv = u.Quantity(rv, unit=rvs.unit).to_value("km/s")
        p.ra = Angle(ras[obj], u.hour).deg
        p.dec = Angle(decs[obj], u.deg).deg
        rapm = float(rapms[obj])
        if not math.isnan(rapm):
            p.rapm = u.Quantity(rapm, unit=rapms.unit).to_value('mas/yr')
        decpm = float(decpms[obj])
        if not math.isnan(decpm):
            p.decpm = u.Quantity(decpm, unit=decpms.unit).to_value('mas/yr')
        for f in objdata.Possible_filters:
            if f == 'z':
                continue
            flux = fluxes[f][obj]
            if not math.isnan(flux):
                p.fluxes[f] = flux
        result.append(p)
    return  result


def add_alias_set(obj, alist):
    """Add set of aliases we just read"""

    global dbcurs, src, verbose

    for aname in alist:
        try:
            obj.add_alias(dbcurs, aname, src, sbok=True)
        except objdata.ObjDataError as e:
            print("Problem with alias", aname, "for", obj.objname, e.args[0], e.args[1], file=sys.stderr)
            sys.exit(252)
        if verbose:
            print("Added alias", aname, "for", obj.objname, file=sys.stderr)


def update_alias_set(fobj, obj):
    """Update alias set taking care of previously manual aliases"""

    global dbcurs, src, verbose

    # Save existing manual aliases and delete all existing ones

    existing_manual_aliases = obj.list_aliases(dbcurs, manonly=True)
    obj.delete_aliases(dbcurs)

    # Remove "main" name from name set and include the rest os aliases, adding back in ones we added before
    # remembering to take out ones we found afresh

    fobj.names.discard(obj.objname)
    mandict = dict()
    for a in existing_manual_aliases:
        mandict[a.aliasname] = a

    manset = set(mandict.keys())
    manset -= fobj.names  # In case we had a previous manual alias in the new set
    add_alias_set(obj, fobj.names)

    # Add back the (remaining) manual aliases

    for manname in manset:
        try:
            obj.add_alias(dbcurs, manname, mandict[manname].source, sbok=False)
        except objdata.ObjDataError as e:
            print("Problem with alias", manname, "for", obj.objname, e.args[0], e.args[1], file=sys.stderr)
            sys.exit(252)
        if verbose:
            print("added manual alias", manname, "for", obj.objname, file=sys.stderr)


def add_new_object(fobj, mainname, target, dispname=None):
    """Add new object and associated alias from search result"""

    global  dbcurs, verbose, src

    obj = objdata.ObjData(objname=mainname, dispname=dispname)
    fobj.names.discard(mainname)
    add_alias_set(obj, fobj.names)
    fobj.update_object(obj)
    obj.vicinity = target
    try:
        obj.put(dbcurs)
    except objdata.ObjDataError as e:
        print("Unexpected error adding new object", obj.objname, "for target", target, e.args[0], e.args[1], file=sys.stderr)
        sys.exit(251)
    if verbose:
        if obj.is_target():
            print("Add target", target, file=sys.stderr)
        else:
            print("Added object", obj.objname, "near to", target, file=sys.stderr)

# Shut up warning messages


warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

parsearg = argparse.ArgumentParser(description='Get objects in vicinity of target object', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('target', nargs=1, type=str, help='Target object')
remdefaults.parseargs(parsearg, tempdir=False)
parsearg.add_argument('--displayname', type=str, help='Display name for target object, default same as name given')
parsearg.add_argument('--radius', type=float, default=30.0, help='Search radius in arcmin')
parsearg.add_argument('--update', action='store_true', help='Updated existing entries default is to abort if we have done it')
parsearg.add_argument('--delete', action='store_true', help='Delete an object and associated aliases')
parsearg.add_argument('--addalias', type=str, help='Add alias of given name')
parsearg.add_argument('--remove', action='store_true', help='Remove the given alias')
parsearg.add_argument('--source', type=str, default='By Hand', help='Source description when adding alias')
parsearg.add_argument('--verbose', action='store_true', help='Give accound of actions"')

resargs = vars(parsearg.parse_args())
target = resargs['target'][0]
remdefaults.getargs(resargs)
displayname = resargs['displayname']
radius = resargs['radius']
update = resargs['update']
delete = resargs['delete']
remove = resargs['remove']
addalias = resargs['addalias']
source = resargs['source']
verbose = resargs['verbose']

if delete:
    shouldexist = True
    if update:
        print("Cannot have --update and --delete", file=sys.stderr)
        sys.exit(10)
    if remove:
        print("Cannot have --remove as well as --delete", file=sys.stderr)
        sys.exit(10)
    if addalias is not None:
        print("Cannot have --addalias as well as --delete", file=sys.stderr)
        sys.exit(10)
elif update:
    shouldexist = True
    if remove:
        print("Cannot have --remove as well as --update", file=sys.stderr)
        sys.exit(10)
    if addalias is not None:
        print("Cannot have --addalias as well as --update", file=sys.stderr)
        sys.exit(10)
elif remove:
    shouldexist = True
    if addalias is not None:
        print("Cannot have --addalias as well as --remove", file=sys.stderr)
        sys.exit(10)
else:
    shouldexist = addalias is not None

dbase, dbcurs = remdefaults.opendb()

dbcurs.execute("SELECT COUNT(*) FROM objdata WHERE objname=%s", target)
nrows = dbcurs.fetchall()

tobj = objdata.ObjData(target)
try:
    tobj.get(dbcurs)
    if addalias is None and not tobj.is_target():
        print(target, "found but as an object in vicinity of", tobj.vicinity, file=sys.stderr)
        sys.exit(11)
    if not shouldexist:
        if tobj.objname == target:
            print(target, "already recorded, use update if needed", file=sys.stderr)
        else:
            print(target, "already recorded as an alias for", tobj.objname, file=sys.stderr)
        sys.exit(11)
    if tobj.objname != target:
        if not remove:
            if verbose:
                print(target, "is an alias for", tobj.objname, file=sys.stderr)
            target = tobj.objname
    elif remove:
        print(target, "is the main name, cannot remove as alias", file=sys.stderr)
        sys.exit(11)
except objdata.ObjDataError:
    if shouldexist:
        print(target, "does not exist in database", file=sys.stderr)
        sys.exit(12)

# Deal first with the cases where we don't have to look up anything

if delete:
    tobj.delete(dbcurs)
    dbase.commit()
    sys.exit(0)

if remove:
    try:
        objdata.Objalias(target).delete(dbcurs)
    except objdata.ObjDataError as e:
        print("Remove failed with error", e.args[0], e.args[1], file=sys.stderr)
        sys.exit(50)
    dbase.commit()
    sys.exit(0)

sb = Simbad()
sb.add_votable_fields('rv_value', 'pm', 'otype', 'distance', 'ids')
for f in objdata.Possible_filters:
    if f != 'z':
        sb.add_votable_fields('flux(' + f.upper() + ')')

if addalias is not None:
    try:
        oname = objdata.get_objname(dbcurs, addalias)
        if oname == addalias:
            print("Already have", oname, "in as object", file=sys.stderr)
        else:
            print("Already have", addalias, "in as alias for", oname, file=sys.stderr)
        sys.exit(60)
    except objdata.ObjDataError:
        pass
    try:
        tobj.add_alias(dbcurs, addalias, source, sb.query_object(addalias) is not None)
    except objdata.ObjDataError as e:
        print("Problem with alias", addalias, e.args[0], e.args[1], file=sys.stderr)
        sys.exit(252)
    if verbose:
        print("Add alias", addalias, "OK", file=sys.stderr)
    dbase.commit()
    sys.exit(0)

targ_sbq = sb.query_object(target)
if targ_sbq is None:
    print("Cannot find", target, "in Simbad", file=sys.stderr)
    sys.exit(100)

targres_list = parse_sbresult(targ_sbq)
if len(targres_list) != 1:
    print("Expecting target list to be length 1 not", len(targres_list), file=sys.stderr)
    sys.exit(200)

targres = targres_list[0]

n = datetime.datetime.now()
src = n.strftime("Simbad %d/%m/%Y")

if update:
    update_alias_set(targres, tobj)
    if displayname is not None:
        tobj.dispname = displayname
    targres.update_object(tobj)
    tobj.update(dbcurs)
    if verbose:
        print("Updated target", target, file=sys.stderr)
else:
    add_new_object(targres, target, target, displayname)

reglist_sbq = sb.query_region(target, radius=radius * u.arcmin)
if reglist_sbq is None or len(reglist_sbq) == 0:
    print("Could not find in target radius", target, file=sys.stderr)
    sys.exit(10)

reglist = parse_sbresult(reglist_sbq)

if update:
    for fndobj in reglist:
        if target in fndobj.names:
            continue
        # Might be existing object or newly-identified object
        obj = objdata.ObjData(objname=fndobj.mainname)
        try:
            obj.get(dbcurs)
        except objdata.ObjDataError as e:
            if e.args[0][0] != '(':
                print(e.args[0], e.args[1], file=sys.stderr)
                sys.exit(250)
            add_new_object(fndobj, fndobj.mainname, target)
            continue

        # We know about this object get rid of existing aliases and put back in

        update_alias_set(fndobj, obj)
        fndobj.update_object(obj)
        obj.update(dbcurs)
        if verbose:
            print("Updated object", obj.objname, file=sys.stderr)

else:
    # New objects

    for fndobj in reglist:
        if target not in fndobj.names:
            add_new_object(fndobj, fndobj.mainname, target)

dbase.commit()
