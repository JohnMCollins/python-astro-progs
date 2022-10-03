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


def fix_fr_aperture(fres, oapp, aps):
    """Adjust aperture size and row/col in findresult"""
    global dbchanges, dbcurs
    fres.rdiff += oapp.rowdiff
    fres.cdiff += oapp.coldiff
    #print("Changing fr r/c from", fres.row, fres.col, end='')
    # oapp.row+ dbpixoffs.rowoffset, oapp.col+ dbpixoffs.coloffset)
    fres.row = oapp.row# + dbpixoffs.rowoffset
    fres.col = oapp.col# + dbpixoffs.coloffset
    #print("to", fres.row, fres.col)
    fres.adus = oapp.adus
    fres.apsize = aps
    if fres.obj:
        fres.obj.apsize = aps
        fres.obj.update(dbcurs)
        dbchanges += 1


def create_invented_object(edit, rrow, rcol, rapsize, adus):
    """Create an object to insert into the findresults structure with given row, column
    and aperture. This is intended to cope with the case where we have specified the
    aperture and where we have optimised it."""

    global findres, targfr, fitsfile, dbchanges, dbcurs

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
    newobject.put(dbcurs)
    dbchanges += 1

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

# dbpixoffs = remfits.Pixoffsets(obsind=findres.obsind)
# dbpixoffs.get_offsets(dbcurs)

targfr = findres.get_targobj()
if targfr is None:
    print("Target not found in findres file???", file=sys.stderr)
    sys.exit(23)

try:
    efile = objedits.load_edits_from_file(editprefix)
except objedits.ObjEditErr as e:
    print("Could not open edits file", editprefix, "error was", e.args[0])
    sys.exit(15)

frchanges = edchanges = dbchanges = 0

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
        create_invented_object(ed, peakl[0].row, peakl[0].col, ed.apsize, peakl[0].adus)
        frchanges += 1
    elif isinstance(ed, objedits.ObjEdit_Newobj_Calcap):
        peak1 = findres.find_peak(ed.row, ed.col, searchpar)
        if peak1 is None:
            print("Failed to find object near r={:d} c={:d}".format(ed.row, ed.col), file=sys.stderr)
            continue
        oapp = findres.opt_aperture(peak1[0].row, peak1[0].col, searchpar)
        if oapp is None:
            print("Could not find opt aperture for object near r={:d} c={:d}".format(oapp.row, oapp.col), file=sys.stderr)
            continue
        create_invented_object(ed, oapp.row, oapp.col, oapp.apsize, oapp.adus)
        frchanges += 1
    elif isinstance(ed, objedits.ObjEdit_Deldisp):
        fr = get_fr_by_label(ed)
        if fr.obj and fr.obj.objname != fr.obj.dispname:
            fr.obj.dispname = fr.obj.objname
            frchanges += 1
            fr.obj.update(dbcurs)
            dbchanges += 1
    elif isinstance(ed, objedits.ObjEdit_Newdisp):
        fr = get_fr_by_label(ed)
        if fr.obj and fr.obj.dispname != ed.dispname:
            fr.obj.dispname = ed.dispname
            frchanges += 1
            fr.obj.update(dbcurs)
            dbchanges += 1
    elif isinstance(ed, objedits.ObjEdit_Adjap):
        fr = get_fr_by_label(ed)
        if fr.apsize != ed.apsize or (fr.obj and fr.obj.apsize != ed.epsize):
            oapp = findres.opt_aperture(fr.row, fr.col, searchpar, minap=ed.apsize, maxap=ed.apsize)
            if oapp is None:
                print("Could not find object near r={:d} c={:d}".format(fr.row, fr.col), file=sys.stderr)
                continue
            #print("Setting aperature to", ed.apsize)
            fix_fr_aperture(fr, oapp, ed.apsize)
            frchanges += 1
            fr.obj.update(dbcurs)
            dbchanges += 1
    elif isinstance(ed, objedits.ObjEdit_Calcap):
        fr = get_fr_by_label(ed)
        oapp = findres.opt_aperture(fr.row, fr.col, searchpar)
        if oapp is None:
            print("Could not find object near r={:d} c={:d}".format(fr.row, fr.col), file=sys.stderr)
            continue
        if fr.apsize != oapp.apsize or (fr.obj and fr.obj.apsize != oapp.apsize):
            if verbose:
                print("Setting aperature label", ed.oldlabel, "from", fr.obj.apsize, "to", oapp.apsize, file=sys.stderr)
            fix_fr_aperture(fr, oapp, oapp.apsize)
            frchanges += 1
    elif isinstance(ed, objedits.ObjEdit_Displab):
        fr = get_fr_by_label(ed)
        if fr.hide:
            print("Changing label on hidden object", ed.oldlabel, file=sys.stderr)
            continue
        if fr.obj is None:
            print("Changing no identified object on", ed.oldlabel, file=sys.stderr)
            continue
        if fr.obj.valid_label():
            dbchanges += fr.unassign_label(dbcurs)
            frchanges += 1
        else:
            dbchanges += fr.assign_label(dbcurs, findres.get_label_set(dbcurs))
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
if dbchanges != 0:
    mydb.commit()
