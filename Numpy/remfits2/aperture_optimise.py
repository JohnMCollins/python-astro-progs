#!  /usr/bin/env python3

"""Aperture optimise"""

import argparse
import warnings
import sys
import os
import numpy as np
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
import remdefaults
import remfits
import find_results
import objdata
import searchparam
import logs

def get_fitsfile(ind):
    """Get fits file by ID"""
    try:
        fname = "{:s}{:d}.fits.gz".format(prefix, ind)
        logging.set_filename(fname)
        ff = remfits.parse_filearg(fname, dbcurs)
        ff.calc_skylevel(skylevstd)
    except remfits.RemFitsErr:
        logging.write("Could not find file for id", ind)
        raise
    finally:
        logging.set_filename("")
    return ff

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

searchpar = searchparam.load()
parsearg = argparse.ArgumentParser(description='Optimise apertures with various restrictions', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('objects', type=str, nargs='*', help='Objects to optimise for or none to optimise as many as possible')
searchpar.argparse(parsearg)
remdefaults.parseargs(parsearg, tempdir=False, inlib=False)
parsearg.add_argument('--prefix', type=str, default='Proc', help='Prefix for FITS files')
parsearg.add_argument('--dir', type=str, help='Directory for FITS files if not CWD')
parsearg.add_argument('--force', action='store_true', help='Force continue if it seems to be done or half-done')
parsearg.add_argument('--verbose', action='store_true', help='Tell everything')
parsearg.add_argument('--skylevelstd', type=float, default=remfits.DEFAULT_SKYLEVELSTD, help='Theshold level of std devs to include points in sky')
parsearg.add_argument('--minoccs', type=int, default=10, help='Minimum number of occurences to consider for inclusion')
parsearg.add_argument('--vicinity', type=str, help='Vicinity when identifying by label')
logs.parseargs(parsearg)

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
searchpar.getargs(resargs)
logging = logs.getargs(resargs)
force = resargs['force']
verbose = resargs['verbose']
skylevstd = resargs['skylevelstd']
prefix = resargs['prefix']
direc = resargs['dir']
minoccs = resargs['minoccs']
objlist = resargs['objects']
vicinity = resargs['vicinity']

# If we are saving stuff, do so and do not exit

if searchpar.saveparams:
    searchparam.save(searchpar)
    if verbose:
        searchpar.display(sys.stderr)

if direc is not None:
    try:
        os.chdir(direc)
    except OSError as e:
        logging.die(10, "Could not select", direc, "error was", e.args[1])

mydb, dbcurs = remdefaults.opendb()
if vicinity is not None:
    try:
        vicinity = objdata.get_objname(dbcurs, vicinity)
    except objdata.ObjDataError:
        logging.die(11, "Do not understand vicinity", vicinity)

# Lookup of objdata retrieved_objects looks ob objind to objdata struct
# objind_ot_obsind is a list of (obsind, row, col)
# obsind_cache is a cache of the firs files for each obsind

retrieved_objects = dict()
objind_to_obsind = dict()

errors = aps_changed = valid_obs = 0

if len(objlist) == 0:
    dbcurs.execute("SELECT objind,obsind,nrow,ncol FROM findresult WHERE hide=0")
    for objind, obsind, row, col in dbcurs.fetchall():
        if objind in retrieved_objects:
            objd = retrieved_objects[objind]
        else:
            objd = objdata.ObjData(objind=objind)
            objd.get(dbcurs)
            retrieved_objects[objind] = objd
        try:
            fitsf = get_fitsfile(obsind)
        except remfits.RemFitsErr:
            errors += 1
            continue
        if fitsf.from_obsind != obsind:
            logging.write(obsind, "does not match file which is", fitsf.from_obsind)
            errors += 1
            continue
        valid_obs += 1
        if objind not in objind_to_obsind:
            objind_to_obsind[objind] = []
        objind_to_obsind[objind].append((obsind, row, col))

else:

    # Case where we only bother with named objects (by name, label or ind)

    for obj in objlist:

        if obj.isdigit():
            objind = int(obj)
            if objind in retrieved_objects:
                continue
            objd = objdata.ObjData(objind=objind)
            try:
                objd.get(dbcurs)
            except objdata.ObjDataError as e:
                logging.write("Could not find object id", objind, "error", e.args[0])
                errors += 1
                continue
            retrieved_objects[objind] = objd
        else:
            if len(obj) <= 4:
                if vicinity is None:
                    logging.write("No vicinity specified for label")
                    errors += 1
                    continue
                objd = objdata.ObjData(vicinity=vicinity, label=obj)
            else:
                try:
                    name = objdata.get_objname(dbcurs, obj)
                except objdata.ObjDataError:
                    logging.write("Unknown name", obj)
                    errors += 1
                    continue
                objd = objdata.ObjData(objname = name)
            try:
                objd.get(dbcurs)
            except objdata.ObjDataError as e:
                logging.write("Could not find object", obj, e.args[0])
                errors += 1
                continue
            objind = objd.objind
            if objind in retrieved_objects:
                continue
            retrieved_objects[objind] = objd

    # Now have list of things to look at, search for find results from those

    if len(retrieved_objects) == 0:
        logging.die(15, "No objects found to process")

    for objind in retrieved_objects:
        dbcurs.execute("SELECT obsind,nrow,ncol FROM findresult WHERE hide=0 AND objind={:d}".format(objind))
        for obsind, row, col in dbcurs.fetchall():
            try:
                fitsf = get_fitsfile(obsind)
            except remfits.RemFitsErr:
                errors += 1
                continue
            if fitsf.from_obsind != obsind:
                logging.write(obsind, "does not match file which is", fitsf.from_obsind)
                errors += 1
                continue
            valid_obs += 1
            if fitsf is None:
                logging.write("Skipping reference to unread obsind", obsind)
                errors += 1
                continue

            if objind not in objind_to_obsind:
                objind_to_obsind[objind] = []
            objind_to_obsind[objind].append((obsind, row, col))

if len(retrieved_objects) == 0:
    logging.die(50, "No objects found to consider")
if valid_obs == 0:
    logging.die(51, "No observations to consider")

# Check we'have got enough to worry about
# If the object is in one we specified, take as error

to_delete = set()
for objind, obslist in objind_to_obsind.items():
    if len(obslist) < minoccs:
        if len(objlist) != 0 or verbose:
            logging.write("Too few ({:d}) occurences of {:s}, ignoring".format(len(obslist), retrieved_objects[objind].dispname))
        if len(objlist) != 0:
            errors += 1
        to_delete.add(objind)

for objind in to_delete:
    del retrieved_objects[objind]
    del objind_to_obsind[objind]

if len(retrieved_objects) == 0:
    logging.die(52, "No objects left to consider")

calculated_apertures = dict()
for objind in retrieved_objects:
    calculated_apertures[objind] = []

for objind, obslist in objind_to_obsind.items():
    for obsind, row, col in obslist:
        try:
            fitsf = get_fitsfile(obsind)
        except remfits.RemFitsErr:
            continue
        findres = find_results.FindResults(fitsf)
        try:
            optapp = findres.opt_aperture(row, col, searchpar)
        except find_results.FindResultErr as e:
            if len(objlist) != 0 or verbose:
                obj = retrieved_objects[objind]
                if obj.valid_label():
                    lab = obj.label
                else:
                    lab = "-"
                logging.write("Could not find aperture for {:s} ({:s}) (previously {:.2f})".format(obj.dispname, lab, obj.apsize))
            if len(objlist) != 0:
                errors += 1
            continue
        calculated_apertures[objind].append((obsind, optapp))

to_delete = set()

for objind, aplist in calculated_apertures.items():
    if len(aplist) < minoccs:
        if len(objlist) != 0 or verbose:
            obj = retrieved_objects[objind]
            if obj.valid_label():
                lab = obj.label
            else:
                lab = "-"
            logging.write("Too few ({:d}) occurences left for {:s} ({:s}), discarding".format(len(aplist), obj.dispname, lab))
        if len(objlist) != 0:
            errors += 1
        to_delete.add(objind)

for objind in to_delete:
    del retrieved_objects[objind]
    try:
        del objind_to_obsind[objind]
    except KeyError:
        pass
    try:
        del calculated_apertures[objind]
    except KeyError:
        pass

if len(calculated_apertures) == 0:
    logging.die(53, "Nothing left to do after calculating apertures")

haslabel = dict()
nolabel = dict()

for objind, aplist in calculated_apertures.items():

    obj = retrieved_objects[objind]
    aps = np.array([a for oi, a in aplist])

    if obj.valid_label():
        if obj.label not in haslabel:
            haslabel[obj.label] = []
        haslabel[obj.label].append((obj.dispname, obj.apsize, aps.mean(), aps.std()))
    else:
        if obj.dispname not in nolabel:
            nolabel[obj.dispname] = []
        nolabel[obj.dispname].append((obj.dispname, obj.apsize, aps.mean(), aps.std()))

for lab in sorted(haslabel.keys(), key=lambda x: x.rjust(4)):
    for dname, existap, meanap, stdap in sorted(haslabel[lab], key=lambda x: x[0]):
        print("{:<4s} {:<16s} {:6.2f} {:6.2f} {:6.2f}".format(lab, dname, existap, meanap, stdap))

for dname in sorted(nolabel.keys()):
    for dummy, existap, meanap, stdap in sorted(nolabel[dname].keys()):
        print("     {:<16s} {:6.2f} {:6.2f} {:6.2f}".format(dname, existap, meanap, stdap))

if errors > 0:
    logging.write(errors, "errors")
    if not force:
        logging.die(50, "Aborting use --force if needed")

nupd = 0
for objind, aplist in calculated_apertures.items():

    obj = retrieved_objects[objind]
    aps = np.array([a for oi, a in aplist])

    nupd += dbcurs.execute("UPDATE objdata SET apsize={:.2f},apstd={:.2f},basedon={:d} WHERE ind={:d}".format(aps.mean(),aps.std(),aps.size,objind))
    mydb.commit()

logging.write(nupd, "updates")
