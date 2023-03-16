#!  /usr/bin/env python3

"""List aperture optimisation results for given objects"""

import argparse
import warnings
import sys
import os
from multiprocessing import Pool
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
import col_from_file
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

def do_optimise(fr):
    """Optimise an object aperture"""
    try:
        optaplist = findres.opt_aperture_list(fr.row, fr.col, searchpar)
    except find_results.FindResultErr:
        return  None

    fname = "{:d}-{:d}.apopt".format(fr.obsind, fr.objind)
    if os.path.exists(fname) and not force:
        logging.write(fname, "exists use --force if needed")
        return  ""
    try:
        with open(fname, 'w') as fout:
            for oa in optaplist:
                fout.write("{:.2f} {:16.10e} {:16.10e} {:16.10e} {:16.10e} {:16.10e}\n".format(oa.apsize, oa.adus, oa.amp, oa.sigma, oa.ampstd, oa.sigmastd))
        return  fname
    except  IOError as e:
        logging.write("Write to", fname, "failed error was", e.args[0])
        return ""

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

searchpar = searchparam.load()
parsearg = argparse.ArgumentParser(description='Generate optimised aperture list with various restrictions', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('obsids', type=int, nargs='*', help='List of obs ids or use stdin')
parsearg.add_argument('--colnum', type=int, default=0, help='Column number to take from standard input')
parsearg.add_argument('--objects', type=str, required=True, nargs='+', help='Objects to optimise for')
parsearg.add_argument('--force', action='store_true', help='Force overwrite if file exists')
searchpar.argparse(parsearg)
remdefaults.parseargs(parsearg, tempdir=False, inlib=False)
parsearg.add_argument('--fitsdir', type=str, help='FITS directory if not CWD')
parsearg.add_argument('--prefix', type=str, default='Proc', help='Prefix for FITS files')
parsearg.add_argument('--outdir', type=str, help='Output directory if not CWD')
parsearg.add_argument('--skylevelstd', type=float, default=remfits.DEFAULT_SKYLEVELSTD, help='Theshold level of std devs to include points in sky')
parsearg.add_argument('--vicinity', type=str, help='Vicinity when identifying by label')
parsearg.add_argument('--maxproc', type=int, default=8, help='Maximum number of processes to run')
logs.parseargs(parsearg)

resargs = vars(parsearg.parse_args())

obsids = resargs["obsids"]
if len(obsids) == 0:
    obsids = map(int, col_from_file.col_from_file(sys.stdin, resargs['colnum']))

force = resargs['force']
objects = resargs['objects']
remdefaults.getargs(resargs)
searchpar.getargs(resargs)
logging = logs.getargs(resargs)
skylevstd = resargs['skylevelstd']
prefix = resargs['prefix']
fitsdir = resargs['fitsdir']
outdir = resargs['outdir']
vicinity = resargs['vicinity']
maxproc = resargs['maxproc']

# If we are saving stuff, do so and exit

if searchpar.saveparams:
    searchparam.save(searchpar)
    sys.exit(0)

currdir = os.getcwd()
if fitsdir is not None:
    afitsdir = os.path.abspath(fitsdir)
    if not os.path.isdir(fitsdir):
        logging.die(10, fitsdir, "is not a directory")
    prefix = os.path.join(afitsdir, prefix)

if outdir is not None:
    aoutdir = os.path.abspath(outdir)
    if currdir != aoutdir:
        if not os.path.isdir(outdir):
            try:
                os.mkdir(outdir)
            except OSError as e:
                logging.die(11, "Could not create", outdir, "error was", e.args[1])
        prefix = os.path.abspath(prefix)
        try:
            os.chdir(outdir)
        except OSError as e:
            logging.die(12, "Could not change to", outdir, "error was", e.args[1])

mydb, dbcurs = remdefaults.opendb()

if vicinity is not None:
    try:
        vicinity = objdata.get_objname(dbcurs, vicinity)
    except objdata.ObjDataError:
        logging.die(13, "Do not understand vicinity", vicinity)

# Object list cache - any order, but we aim to avoid duplications

objlist = dict()
errors = 0

for obj in objects:
    if obj.isdigit():
        objind = int(obj)
        if objind in objlist:
            logging.write("Duplicated objind", objind)
            continue
        objd = objdata.ObjData(objind=objind)
        try:
            objd.get(dbcurs)
        except objdata.ObjDataError as e:
            logging.write("Could not find object id", objind, "error", e.args[0])
            errors += 1
            continue
        objlist[objind] = objd
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
            objd = objdata.ObjData(name=name)
        try:
            objd.get(dbcurs)
        except objdata.ObjDataError as e:
            logging.write("Could not find object", obj, e.args[0])
            errors += 1
            continue
        objind = objd.objind
        if objind in objlist:
            logging.write("Duplicated object", objd.dispname)
            continue
        objlist[objind] = objd

if len(objlist) == 0:
    logging.die(14, "No objects found to process")

if errors != 0:
    logging.die(15, "Aborting due to errors")

# Make list of files we've created in case we delete later

madelist = set()

for obsind in obsids:

    try:
        ff = get_fitsfile(obsind)
    except remfits.RemFitsErr as e:
        errors += 1
        continue

    findres = find_results.FindResults(ff)
    findres.loaddb(dbcurs)

    opt_list = []

    for fr in findres.results():
        if fr.objind in objlist:
            opt_list.append(fr)

    while len(opt_list) != 0:
        lng = len(opt_list)
        if lng == 1:
            fmade = do_optimise(opt_list.pop(0))
            if fmade is not None:
                if fmade == "":
                    errors += 1
                else:
                    madelist.add(fmade)
        else:
            seg = opt_list[:maxproc]
            opt_list = opt_list[maxproc:]
            with Pool(min(len(seg), maxproc)) as p:
                results = p.map(do_optimise, seg)
                for r in results:
                    if r is not None:
                        if r == "":
                            errors += 1
                        else:
                            madelist.add(r)

if errors != 0:
    for m in madelist:
        os.remove(m)
