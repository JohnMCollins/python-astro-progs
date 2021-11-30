#!  /usr/bin/env python3

"""Fix objloc and finds after updating object aperture or suppress flag"""

import argparse
import sys
import os
import glob
import warnings
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
import remdefaults
import objdata
import find_results
import obj_locations
import remfits
import miscutils

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

parsearg = argparse.ArgumentParser(description='Fix find files after updating aperture or suppress flag', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('objects', type=str, nargs='+', help='Objects to adjust')
remdefaults.parseargs(parsearg, tempdir=False, inlib=False)
parsearg.add_argument('--directory', type=str, help='Directory if not current')
parsearg.add_argument('--shiftmax', type=int, default=4, help='Maxmimum shift of centre')

resargs = vars(parsearg.parse_args())
objects = resargs['objects']
remdefaults.getargs(resargs)
direc = resargs['directory']
shiftmax = resargs['shiftmax']

if direc:
    os.chdir(direc)

db, mycurs = remdefaults.opendb()

obstr_list = dict()
errors = 0
vicinities = set()

for obj in objects:

    try:
        objstr = objdata.ObjData(obj)
        objstr.get(mycurs, allobj=True)
    except objdata.ObjDataError as e:
        print("Cannot find", obj, "error was", e.args[0], e.args[1], file=sys.stderr)
        errors += 1
        continue
    obstr_list[objstr.objname] = objstr
    vicinities.add(objstr.vicinity)

if errors > 0 or len(obstr_list) == 0:
    print("Aborting due to errors", file=sys.stderr)
    sys.exit(10)

for file in glob.iglob('*.objloc'):

    olocf = obj_locations.load_objlist_from_file(file)
    changes = 0
    dlist = []
    for n, cobj in enumerate(olocf.results()):
        try:
            dbobj = obstr_list[cobj.name]
        except KeyError:
            continue
        if dbobj.suppress:
            dlist.append(n)
            changes += 1
        if dbobj.apsize != cobj.apsize:
            cobj.apsize = dbobj.apsize
            changes += 1

    # Delete the newly-suppressed stuff
    # Note this empties dlist
    # Do this backwards so as not to mess up indices

    while len(dlist) != 0:
        olocf.resultlist.pop(dlist.pop())

    if changes != 0:
        obj_locations.save_objlist_to_file(olocf, file, force=True)

    pref = miscutils.removesuffix(file, 'objloc')
    try:
        fitsfile = remfits.parse_filearg(pref, mycurs)
    except remfits.RemFitsErr:
        continue

    skylevel = fitsfile.meanval

    try:
        findres = find_results.load_results_from_file(pref, fitsfile)
    except find_results.FindResultErr:
        continue

    # dlist = [] not needed as we popped everything above
    changes = 0
    for n, fr in enumerate(findres.results()):
        try:
            dbobj = obstr_list[fr.name]
        except KeyError:
            continue
        if dbobj.suppress:
            dlist.append(n)
            changes += 1
        elif dbobj.apsize != fr.apsize:
            optap = findres.findbest_colrow(fr.col, fr.row, dbobj.apsize, shiftmax)
            fr.col, fr.row, aduc, npix = optap
            fr.adus = aduc - npix * skylevel
            fr.apsize = dbobj.apsize
            changes += 1
    while len(dlist) != 0:
        findres.resultlist.pop(dlist.pop())
    if changes != 0:
        findres.reorder()
        findres.relabel()
        find_results.save_results_to_file(findres, pref, force=True)
