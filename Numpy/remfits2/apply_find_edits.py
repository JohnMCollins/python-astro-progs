#!  /usr/bin/env python3

"""Apply edits to image"""

import argparse
import warnings
import sys
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
import remdefaults
import remfits
import obj_locations
import find_results
import objedits

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

parsearg = argparse.ArgumentParser(description='Apply edits created by display image to single result', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('file', nargs=1, type=str, help='Image file')
parsearg.add_argument('--objloc', type=str, help='Name for object locations file if to be different from image file name')
parsearg.add_argument('--findres', type=str, help='Name for find results file if to be different from image file name')
parsearg.add_argument('--edits', type=str, help='Edits file name if different from findres file name')
remdefaults.parseargs(parsearg, tempdir=False, inlib=False)
parsearg.add_argument('--force', action='store_true', help='Force continue if it seems to be done or half-done')
parsearg.add_argument('--updatedb', action='store_true', help='Update DB with results')
parsearg.add_argument('--apsize', type=int, default=6, help='Aperature size to use if none assigned')
parsearg.add_argument('--totsign', type=float, default=find_results.DEFAULT_TOTSIGN, help='Total significance')
parsearg.add_argument('--maxshift', type=int, default=7, help='Maximum pixel displacement looking for objects first pass')
parsearg.add_argument('--maxap', type=int, default=20, help='Maximum aperture size to use')
parsearg.add_argument('--minap', type=int, default=3, help='Minimum aperture size to use')

resargs = vars(parsearg.parse_args())
infilename = resargs['file'][0]
objlocprefix = resargs['objloc']
findresprefix = resargs['findres']
editprefix = resargs['edits']
remdefaults.getargs(resargs)
force = resargs['force']
updatedb = resargs['updatedb']
apsize = resargs['apsize']
minap = resargs['minap']
maxap = resargs['maxap']
totsign = resargs['totsign']
maxshift = resargs['maxshift']

mydb, dbcurs = remdefaults.opendb()

try:
    fitsfile = remfits.parse_filearg(infilename, dbcurs)
except remfits.RemFitsErr as e:
    print(e.args[0], file=sys.stderr)
    sys.exit(52)

if objlocprefix is None:
    if infilename.isdigit():
        print("Need to give objloc file name when image file", infilename, "given as digits", file=sys.stderr)
        sys.exit(10)
    objlocprefix = infilename

if findresprefix is None:
    if infilename.isdigit():
        print("Need to give find results file name when image file", infilename, "given as digits", file=sys.stderr)
        sys.exit(11)
    findresprefix = infilename

if editprefix is None:
    editprefix = findresprefix

editprefix = remdefaults.edits_file(editprefix)

# Now open all the files

try:
    objlocfile = obj_locations.load_objlist_from_file(objlocprefix, fitsfile)
except obj_locations.ObjLocErr as e:
    print("Unable to load objloc file, error was", e.args[0], file=sys.stderr)
    sys.exit(12)

if objlocfile.num_results() == 0:
    print("No results in objloc file", objlocprefix, file=sys.stderr)
    sys.exit(13)

try:
    findres = find_results.load_results_from_file(findresprefix, fitsfile)
except find_results.FindResultErr as e:
    print("Unable to load findres file, error was", e.args[0], file=sys.stderr)
    sys.exit(14)

try:
    efile = objedits.load_edits_from_file(editprefix)
except objedits.ObjEditErr as e:
    print("Could not open edits file", editprefix, "error was", e.args[0])
    sys.exit(15)

frchanges = edchanges = dbchanges = 0

for ed in efile.editlist:
    if ed.done and not force:
        continue

    if isinstance(ed, objedits.ObjEdit_Hide):
        try:
            fr = findres[ed.oldlabel]
        except KeyError:
            print("Did not find label {:s} in findres file".format(ed.oldlabel), file=sys.stderr)
            sys.exit(20)
        if fr.obj is None:
            print("No corresponding object for label {:s} in findres file".format(ed.oldlabel), file=sys.stderr)
            sys.exit(21)
        if fr.obj.objind != ed.objid:
            print("Fr objind of {:d} is not same as in edit {:d} for label {:s}".format(fr.obj.objind, ed.objid, ed.oldlabel), file=sys.stderr)
            sys.exit(22)
        if not fr.hide:
            fr.hide = True
            frchanges += 1
        if not ed.done:
            ed.done = True
            edchanges += 1
    elif isinstance(ed, objedits.ObjEdit_Newobj_Ap):
        print("I don't know how to handle new objects spec aperature yet", file=sys.stderr)
    elif isinstance(ed, objedits.ObjEdit_Newobj_Calcap):
        print("I don't know how to handle new objects calc aperature yet", file=sys.stderr)
    elif isinstance(ed, objedits.ObjEdit_Deldisp):
        print("I don't know how to handle delete dispnme yet", file=sys.stderr)
    elif isinstance(ed, objedits.ObjEdit_Newdisp):
        print("I don't know how to handle new dispname yet", file=sys.stderr)
    elif isinstance(ed, objedits.ObjEdit_Adjap):
        print("I don't know how to handle adjust aperture yet", file=sys.stderr)
    elif isinstance(ed, objedits.ObjEdit_Calcap):
        print("I don't know how to handle calculate aperture yet", file=sys.stderr)
    else:
        print("Unknown edit tyupe in file", efile, file=sys.stderr)
        sys.exit(50)

if updatedb:
    for fr in findres.results(idonly=True):
        if fr.hide:
            dbchanges += dbcurs.execute("UPDATE objdata SET suppress=1 WHERE ind={:d}".format(fr.obj.objind))

if frchanges != 0:
    find_results.save_results_to_file(findres, findresprefix, force=True)
    print(frchanges, "changes to findres file", file=sys.stderr)
if edchanges != 0:
    objedits.save_edits_to_file(efile, editprefix)
    print(edchanges, "changes to edits file", file=sys.stderr)
if dbchanges != 0:
    mydb.commit()
    print(dbchanges, "database updates", file=sys.stderr)
