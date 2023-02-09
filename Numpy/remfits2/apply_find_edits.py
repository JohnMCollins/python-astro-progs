#!  /usr/bin/env python3

"""Apply edits to image"""

import argparse
import warnings
import sys
import os.path
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
import remdefaults
import remfits
import find_results
import objedits
import objdata
import searchparam
import logs


def fix_fr_aperture(fres):
    """Adjust aperture size and row/col in findresult.
    Return true/false if found/not found"""

    # We already set the specified or calculated aperture size in the aperture record
    # Get starting row/col from coords which should have been set up originally

    expcol, exprow = fitsfile.wcs.coords_to_colrow(fres.obj.ra, fres.obj.dec)
    print("fix_fr_aperture col={:.4f} row={:.4f}".format(expcol, exprow))

    # Now try to find the object again

    try:
        newfr = findres.find_object(exprow, expcol, fres.obj, searchpar)
    except find_results.FindResultErr as err:
        logging.write("Unable to re-find {:s} after setting aperture to {:.2f}\n    error was {:s}".format(fres.obj.dispname,
                                                                                                                    fres.obj.apsize,
                                                                                                                    err.args[0]))
        return False

    fres.col = newfr.col
    fres.row = newfr.row
    fres.rdiff = newfr.rdiff
    fres.cdiff = newfr.cdiff
    fres.xoffstd = newfr.xoffstd
    fres.yoffstd = newfr.yoffstd
    fres.amp = newfr.amp
    fres.sigma = newfr.sigma
    fres.ampstd = newfr.ampstd
    fres.sigmastd = newfr.sigmastd
    fres.adus = newfr.adus
    fres.modadus = newfr.modadus
    fres.apsize = fres.obj.apsize
    fres.obj.update(dbcurs)
    fres.update(dbcurs)
    return True

def make_new_possobj(ed, apsize = None):
    """Put together a putative new object"""
    if objdata.nameused(dbcurs, ed.objname, allobj=True):
        logging.write(ed.objname, "already in use")
        return  None

    pobj = objdata.ObjData(objname=ed.objname,
                           dispname=ed.dispname,
                           latexname=ed.latexname,
                           vicinity=vicinity,
                           invented=True,
                           objtype='Unknown',
                           usable=True)
    if apsize is not None:
        pobj.apsize = apsize
    return  pobj

def create_invented_object(fres, newobject):
    """Complete creation of invented object"""

    # Assume that the peak we just found is offset by as much as the target
    # Get the RA/DEC according to what they would have been if the peak was not offset by that.

    try:
        newfr = findres.find_object(fres.row, fres.col, newobj, searchpar)
    except find_results.FindResultErr as err:
        logging.write("Could not relocate object error was", err.args[0])
        return  False

    newfr.radeg, newfr.decdeg = fitsfile.wcs.colrow_to_coords(newfr.col, newfr.row)
    newfr.rdiff = newfr.cdiff = 0.0
    newfr.obj.ra = newfr.radeg
    newfr.obj.dec = newfr.decdeg
    newfr.obj = newobject
    findres.resultlist.append(newfr)
    newobject.put(dbcurs)
    return  True

# Shut up warning messages


warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

searchpar = searchparam.load()
parsearg = argparse.ArgumentParser(description='Apply edits from image display/markobj', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
searchpar.argparse(parsearg)
remdefaults.parseargs(parsearg, tempdir=False, inlib=False)
parsearg.add_argument('--force', action='store_true', help='Force continue if it seems to be done or half-done')
parsearg.add_argument('--verbose', action='store_true', help='Tell everything')
parsearg.add_argument('--skylevelstd', type=float, default=remfits.DEFAULT_SKYLEVELSTD, help='Theshold level of std devs to include points in sky')
logs.parseargs(parsearg)

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
searchpar.getargs(resargs)
force = resargs['force']
verbose = resargs['verbose']
skylevstd = resargs['skylevelstd']
logging = logs.getargs(resargs)

# If we are saving stuff, do so and do not exit

if searchpar.saveparams:
    searchparam.save(searchpar)
    if verbose:
        searchpar.display(sys.stderr)

mydb, dbcurs = remdefaults.opendb()

elist = objedits.ObjEdit_List()
elist.loaddb(dbcurs)                # Don't include done ones

if elist.num_edits() == 0:
    logging.die(1, "No edits to process")

# Map fitsfiles to remfits object

filesseen = dict()
lastfile = ""
lastfits = lastfind = targfr = lastvic = None

errors = numdone = dbchanges = 0

for edit in elist.get_next():

    infilename = edit.obsfile
    if  lastfile != infilename:
        logging.set_filename(os.path.basename(infilename))

        if infilename in filesseen:
            fitsfile, findres, vicinity = filesseen[infilename]
        else:
            try:
                fitsfile = remfits.parse_filearg(infilename, dbcurs)
                fitsfile.calc_skylevel(skylevstd)
            except remfits.RemFitsErr as e:
                logging.write("Could not open", e.args[0])
                errors += 1
                logging.set_filename(os.path.basename(lastfile))
                infilename = lastfile
                continue
            try:
                vicinity = objdata.get_objname(dbcurs, fitsfile.target, allobj=True)
            except objdata.ObjDataError as e:
                logging.write("Cannot find vicinity", fitsfile.target, e.args[0])
                errors += 1
                logging.set_filename(os.path.basename(lastfile))
                infilename = lastfile
                fitsfile = lastfits
                continue
            findres = find_results.FindResults(fitsfile)
            findres.loaddb(dbcurs)
            targfr = findres.get_targobj()
            if targfr is None:
                logging.write("Target not found in find results???")
                errors += 1
                infilename = lastfile
                fitsfile = lastfits
                vicinity = lastvic
                findres = lastfind
                continue
            filesseen[infilename] = (fitsfile, findres, vicinity)
        lastfile = infilename
        lastfits = fitsfile
        lastfind = findres
        lastvic = vicinity

    if edit.op == "HIDE":
        fr = findres.get_by_objind(edit.objind)
        if  fr is None:
            logging.write("Unable to find objind {:d}".format(edit.objind))
            errors += 1
            continue
        if fr.hide:
            logging.write("objind {:d} for {:s} already hidden".format(edit.objind, fr.obj.dispname))
            errors += 1
            continue
        fr.hide = True
        dbchanges += fr.update(dbcurs)
    elif edit.op == "NEW":
        newobj = make_new_possobj(edit, edit.apsize)
        if newobj is None:
            errors += 1
            continue
        fr = findres.find_peak(edit.row, edit.col, newobj, searchpar)
        if fr is None:
            logging.write("Failed to find object near r={:d} c={:d}".format(edit.row, edit.col))
            errors += 1
            continue
        if not create_invented_object(fr, newobj):
            continue
        dbchanges += 1
    elif edit.op == "NEWAP":
        newobj = make_new_possobj(edit, None)
        if newobj is None:
            errors += 1
            continue
        fr = findres.find_peak(edit.row, edit.col, newobj, searchpar)
        if fr is None:
            logging.write("Failed to find object near r={:d} c={:d}".format(edit.row, edit.col))
            errors += 1
            continue
        try:
            oapp = findres.opt_aperture(fr.row, fr.col, searchpar)
            newobj.apsize = oapp
        except find_results.FindResultErr:
            logging.write("Could not find opt aperture for object near r={:d} c={:d}".format(edit.row, edit.col))
            errors += 1
            continue
        if not create_invented_object(fr, newobj):
            continue
        dbchanges += 1
    elif edit.op == "DELDISP":
        fr = findres.get_by_objind(edit.objind)
        if  fr is None:
            logging.write("Unable to find objind {:d}".format(edit.objind))
            errors += 1
            continue
        if fr.obj.objname != fr.obj.dispname or fr.obj.objname != fr.obj.latexname:
            fr.obj.latexname = fr.obj.dispname = fr.obj.objname
            fr.obj.update(dbcurs)
            dbchanges += 1
    elif edit.op == "NEWDISP":
        fr = findres.get_by_objind(edit.objind)
        if  fr is None:
            logging.write("Unable to find objind {:d}".format(edit.objind))
            errors += 1
            continue
        fr.obj.dispname = edit.dispname
        fr.obj.latexname = edit.latexname
        fr.obj.update(dbcurs)
        dbchanges += 1
    elif edit.op == "SETAP":
        fr = findres.get_by_objind(edit.objind)
        if  fr is None:
            logging.write("Unable to find objind {:d}".format(edit.objind))
            errors += 1
            continue
        if fr.obj.apsize != edit.apsize:
            fr.obj.apsize = edit.apsize
            fr.obj.update(dbcurs)
            if not fix_fr_aperture(fr):
                continue
            dbchanges += 1
    elif edit.op == "CALCAP":
        fr = findres.get_by_objind(edit.objind)
        if  fr is None:
            logging.write("Unable to find objind {:d}".format(edit.objind))
            errors += 1
            continue
        try:
            logging.write("opt_aperture col={:.4f} row={:.4f}".format(fr.col, fr.row))
            bestap = findres.opt_aperture(fr.row, fr.col, searchpar)
        except find_results.FindResultErr as e:
            logging.write("Could not find best aperture for", fr.obj.dispname, e.args[0])
            errors += 1
            # Set so we won't get stuck on it.
            edit.setdone(dbcurs)
            dbchanges += 1
            continue
        if fr.obj.apsize is None or round(fr.obj.apsize, 2) != round(bestap, 2):
            if verbose:
                if fr.obj.apsize is None:
                    logging.write("Setting aperture of {:s} to {:.2f} initially not set".format(fr.obj.dispname, bestap))
                else:
                    logging.write("Setting aperture of {:s} to {:.2f} previously {:.2f}".format(fr.obj.dispname, bestap, fr.obj.apsize))
            fr.obj.apsize = round(bestap, 2)
            fr.obj.update(dbcurs)
            if not fix_fr_aperture(fr):
                continue
            dbchanges += 1
    else:
        logging.die(50, "Unknown edit type", edit.op)
    edit.setdone(dbcurs)
    dbchanges += 1

if dbchanges != 0:
    mydb.commit()
