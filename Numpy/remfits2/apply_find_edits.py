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
import objdata
import searchparam


def get_fr_by_label(edit):
    """Point to findresult structure by label"""
    global findres
    try:
        fres = findres[edit.oldlabel]
    except KeyError:
        print("Did not find label {:s} in findres file".format(edit.oldlabel), file=sys.stderr)
        sys.exit(20)
    if fres.obj is None:
        print("No corresponding object for label {:s} in findres file".format(edit.oldlabel), file=sys.stderr)
        sys.exit(21)
    if fres.obj.objind != edit.objid:
        print("Fr objind of {:d} is not same as in edit {:d} for label {:s}".format(fres.obj.objind, edit.objid, edit.oldlabel), file=sys.stderr)
        sys.exit(22)
    return  fres


def fix_fr_aperture(fres, row, col, adus, aps):
    """Adjust aperture size and row/col in findresult"""
    fres.rdiff += row - fres.row
    fres.cdiff += col - fres.col
    fres.row = row
    fres.col = col
    fres.adus = adus
    fres.apsize = aps
    if fres.obj:
        fres.obj.apsize = aps


def create_invented_object(edit, rrow, rcol, rapsize, adus):
    """Create an object to insert into the findresults structure with given row, column
    and aperture. This is intended to cope with the case where we have specified the
    aperture and where we have optimised it."""

    global findres, targfr, fitsfile

    # Assume that the peak we just found is offset by as much as the target
    # Get the RA/DEC according to what they would have been if the peak was not offset by that.

    pra, pdec = fitsfile.wcs.colrow_to_coords(rcol - targfr.cdiff, rrow - targfr.rdiff)
    newobject = objdata.ObjData(name=edit.name,
                                dispname=edit.dispname,
                                vicinity=targfr.obj.objname,
                                objtype="unknown",
                                invented=True,
                                apsize=rapsize,
                                ra=pra,
                                dec=pdec)
    newfindres = find_results.FindResult(radeg=pra,
                                         decdeg=pdec,
                                         col=rcol,
                                         row=rrow,
                                         apsize=rapsize,
                                         adus=adus,
                                         rdiff=targfr.rdiff,
                                         cdiff=targfr.cdiff)
    newfindres.obj = newobject
    findres.resultlist.append(newfindres)

# Shut up warning messages


warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

searchpar = searchparam.load()
parsearg = argparse.ArgumentParser(description='Apply edits created by display image to single result', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('file', nargs=1, type=str, help='Image file')
parsearg.add_argument('--objloc', type=str, help='Name for object locations file if to be different from image file name')
parsearg.add_argument('--findres', type=str, help='Name for find results file if to be different from image file name')
parsearg.add_argument('--edits', type=str, help='Edits file name if different from findres file name')
parsearg.add_argument('--apstep', type=float, default=1.0, help='Step size for optimising apertures')
searchpar.argparse(parsearg)
remdefaults.parseargs(parsearg, tempdir=False, inlib=False)
parsearg.add_argument('--force', action='store_true', help='Force continue if it seems to be done or half-done')
parsearg.add_argument('--verbose', action='store_true', help='Tell everything')

resargs = vars(parsearg.parse_args())
infilename = resargs['file'][0]
objlocprefix = resargs['objloc']
findresprefix = resargs['findres']
editprefix = resargs['edits']
remdefaults.getargs(resargs)
searchpar.getargs(resargs)
force = resargs['force']
verbose = resargs['verbose']
apstep = resargs['apstep']

# If we are saving stuff, do so and do not exit

if searchpar.saveparams:
    searchparam.save(searchpar)
    if verbose:
        searchpar.display(sys.stderr)

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

targfr = findres.get_targobj()
if targfr is None:
    print("Target not found in findres file???", file=sys.stderr)
    sys.exit(23)

try:
    efile = objedits.load_edits_from_file(editprefix)
except objedits.ObjEditErr as e:
    print("Could not open edits file", editprefix, "error was", e.args[0])
    sys.exit(15)

frchanges = edchanges = 0

for ed in efile.editlist:
    if ed.done:
        continue

    if isinstance(ed, objedits.ObjEdit_Hide):
        fr = get_fr_by_label(ed)
        if not fr.hide:
            fr.hide = True
            frchanges += 1
    elif isinstance(ed, objedits.ObjEdit_Newobj_Ap):
        peakl = findres.find_peak(ed.row, ed.col, searchpar, apsize=ed.apsize)
        if peakl is None:
            print("Failed to find object near r={:d} c={:d}".format(ed.row, ed.col), file=sys.stderr)
            continue
        dummy, dummy, trow, tcol, tadus = peak1[0]
        create_invented_object(ed, trow, tcol, ed.apsize, tadus)
        frchanges += 1
    elif isinstance(ed, objedits.ObjEdit_Newobj_Calcap):
        peak1 = findres.find_peak(ed.row, ed.col, searchpar)
        if peak1 is None:
            print("Failed to find object near r={:d} c={:d}".format(ed.row, ed.col), file=sys.stderr)
            continue
        dummy, dummy, trow, tcol, tadus = peak1[0]
        oapp = findres.opt_aperture(trow, tcol, searchpar, step=apstep)
        if oapp is None:
            print("Could not find opt aperture for object near r={:d} c={:d}".format(trow, tcol), file=sys.stderr)
            continue
        aperture, trow, tcol, tadus = oapp
        create_invented_object(ed, trow, tcol, aperture, tadus)
        frchanges += 1
    elif isinstance(ed, objedits.ObjEdit_Deldisp):
        fr = get_fr_by_label(ed)
        if fr.obj and fr.obj.objname != fr.obj.dispname:
            fr.obj.dispname = fr.obj.objname
            frchanges += 1
    elif isinstance(ed, objedits.ObjEdit_Newdisp):
        fr = get_fr_by_label(ed)
        if fr.obj and fr.obj.dispname != ed.dispname:
            fr.obj.dispname = ed.dispname
            frchanges += 1
    elif isinstance(ed, objedits.ObjEdit_Adjap):
        fr = get_fr_by_label(ed)
        if fr.apsize != ed.apsize or (fr.obj and fr.obj.apsize != ed.epsize):
            oapp = findres.opt_aperture(fr.row, fr.col, searchpar, minap=ed.apsize, maxap=ed.apsize)
            if oapp is None:
                print("Could not find object near r={:d} c={:d}".format(fr.row, fr.col), file=sys.stderr)
                continue
            dummy, trow, tcol, tadus = oapp
            fix_fr_aperture(fr, trow, tcol, tadus, ed.apsize)
            frchanges += 1
    elif isinstance(ed, objedits.ObjEdit_Calcap):
        fr = get_fr_by_label(ed)
        oapp = findres.opt_aperture(fr.row, fr.col, searchpar, step=apstep)
        if oapp is None:
            print("Could not find object near r={:d} c={:d}".format(fr.row, fr.col), file=sys.stderr)
            continue
        aperture, trow, tcol, tadus = oapp
        if fr.apsize != aperture or (fr.obj and fr.obj.apsize != aperture):
            fix_fr_aperture(fr, trow, tcol, tadus, aperture)
            frchanges += 1
    else:
        print("Unknown edit tyupe in file", efile, file=sys.stderr)
        sys.exit(50)
    ed.done = True
    edchanges += 1

if frchanges != 0:
    findres.reorder()
    findres.relabel()
    find_results.save_results_to_file(findres, findresprefix, force=True)
    print(frchanges, "changes to findres file", file=sys.stderr)
if edchanges != 0:
    objedits.save_edits_to_file(efile, editprefix)
    print(edchanges, "changes to edits file", file=sys.stderr)
