#!  /usr/bin/env python3

"""Fix magnitudes in findres and objloc files"""

import argparse
import sys
import os
import glob
import remdefaults
import find_results
import obj_locations
import objdata


class magrec:
    """Record mags"""

    def __init__(self):
        for f in objdata.Possible_filters:
            setattr(self, f + 'mag', None)

    def unpack_row(self, row):
        """Unpack row from DB"""
        for n, f in enumerate(objdata.Possible_filters):
            setattr(self, f + 'mag', row[n])

    def copy_datum(self, datum):
        """Copy to objloc or findres"""
        for f in objdata.Possible_filters:
            mag = f + 'mag'
            setattr(datum, mag, getattr(self, mag, None))


parsearg = argparse.ArgumentParser(description='Fix magnitudes in object locations and find results', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg, tempdir=False, inlib=False)
parsearg.add_argument('--directory', type=str, help='Directory if not current')

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
direc = resargs['directory']

if direc:
    os.chdir(direc)

db, mycurs = remdefaults.opendb()

selfld = ",".join([f + 'mag' for f in objdata.Possible_filters])
selfld = "SELECT " + selfld + " FROM objdata WHERE objname=%s"

objdict = dict()

for fil in glob.glob('*.findres'):
    fr = find_results.load_results_from_file(fil)
    for r in fr.results():
        if len(r.name) == 0:
            continue
        try:
            mres = objdict[r.name]
        except KeyError:
            mycurs.execute(selfld, r.name)
            rows = mycurs.fetchall()
            if len(rows) != 1:
                print("Unexpected search result length", len(rows), file=sys.stderr)
                sys.exit(100)
            mres = magrec()
            mres.unpack_row(rows[0])
        mres.copy_datum(r)
    find_results.save_results_to_file(fr, fil, True)

for fil in glob.glob('*.objloc'):
    fr = obj_locations.load_objlist_from_file(fil)
    for r in fr.results():
        try:
            mres = objdict[r.name]
        except KeyError:
            mycurs.execute(selfld, r.name)
            rows = mycurs.fetchall()
            if len(rows) != 1:
                print("Unexpected search result length", len(rows), file=sys.stderr)
                sys.exit(100)
            mres = magrec()
            mres.unpack_row(rows[0])
        mres.copy_datum(r)
    obj_locations.save_objlist_to_file(fr, fil, True)
