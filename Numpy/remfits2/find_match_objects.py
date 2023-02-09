#!  /usr/bin/env python3

"""Find objects in image"""

import argparse
import warnings
import sys
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
import remdefaults
import remfits
import find_results
import searchparam
import objdata
import logs

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

searchpar = searchparam.load()
parsearg = argparse.ArgumentParser(description='Find objects in image after finding target', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('file', nargs=1, type=str, help='Image file')
searchpar.argparse(parsearg)
remdefaults.parseargs(parsearg, tempdir=False, inlib=False)
parsearg.add_argument('--deleteold', action='store_true', help='Delete ones done already')
parsearg.add_argument('--filter', type=str, help='Filter to restrict to')
parsearg.add_argument('--minbri', type=float, default=5, help='Minimum brightness of objects as percentage of target')
parsearg.add_argument('--nogaia', action='store_true', help='Omit listing GAIA objects')
parsearg.add_argument('--verbose', action='count', help='Tell everything')
parsearg.add_argument('--variability', type=float, default=0.0, help='Maximum variability acceptable')
parsearg.add_argument('--skylevelstd', type=float, default=remfits.DEFAULT_SKYLEVELSTD, help='Theshold level of std devs to include points in sky')
parsearg.add_argument('--findmin', type=int, default=10, help='Minimum number to find to consider success')
parsearg.add_argument('--trimleft', type=int, default=0, help='Pixels to trim off left')
parsearg.add_argument('--trimright', type=int, default=0, help='Pixels to trim off right')
parsearg.add_argument('--trimtop', type=int, default=0, help='Pixels to trim off top')
parsearg.add_argument('--trimbottom', type=int, default=0, help='Pixels to trim off bottom')
logs.parseargs(parsearg)

resargs = vars(parsearg.parse_args())
infilename = resargs['file'][0]
remdefaults.getargs(resargs)
searchpar.getargs(resargs)
deleteold = resargs['deleteold']
filt = resargs['filter']
minbri = resargs['minbri']
nogaia = resargs['nogaia']
maxvar = resargs['variability']
verbose = resargs['verbose']
if verbose is None:
    verbose = 0
findmin = resargs['findmin']
skylevstdp = resargs['skylevelstd']
trimbottom = resargs['trimbottom']
trimleft = resargs['trimleft']
trimright = resargs['trimright']
trimtop = resargs['trimtop']
logging = logs.getargs(resargs)

# If we are saving stuff, do so and exit

if searchpar.saveparams:
    searchparam.save(searchpar)
    if verbose:
        searchpar.display(sys.stderr)
    sys.exit(0)

mydb, dbcurs = remdefaults.opendb()

logging.set_filename(infilename)

try:
    fitsfile = remfits.parse_filearg(infilename, dbcurs)
    fitsfile.calc_skylevel(skylevstdp)
except remfits.RemFitsErr as e:
    logging.die(52, e.args[0])

if filt is not None and fitsfile.filter not in filt:
    logging.die(53, "is for filter", fitsfile.filter, "not in specified", filt)

try:
    findres = find_results.FindResults(fitsfile)
    findres.loaddb(dbcurs)
except find_results.FindResultErr as e:
    logging.die(14, "Could not load find results, error was", e.args[0])

num_existing = findres.num_results()

if num_existing == 0:
    logging.die(15, "No results in findres file, expecting at least 1 for target")

targfr = findres[0]

if not targfr.istarget:
    logging.die(17, "No target (should be first) in findres file")

# Get objects in vicinity

objlist = objdata.get_sky_region(dbcurs, fitsfile, maxvar)
coordlist = [(obj.ra, obj.dec) for obj in objlist]
pixlist = fitsfile.wcs.coords_to_pix(coordlist)
maxrow = fitsfile.nrows - trimtop
maxcol = fitsfile.ncolumns - trimright

# Build new results list

newfrlist = [targfr]
donealready = notfound = newones = 0

for obj, pixes in zip(objlist, pixlist):
    if not deleteold:
        try:
            fr = findres[obj.objname]
            if verbose > 1:
                logging.write("Done", obj.dispname, "already")
            newfrlist.append(fr)
            donealready += 1
            continue
        except find_results.FindResultErr:
            pass
    pcol, prow = pixes
    if  pcol < trimleft or prow < trimbottom or pcol >= maxcol or prow >= maxrow or obj.is_target():
        if verbose > 1:
            logging.write(obj.dispname, "not in image")
        continue
    try:
        newfr = findres.find_object(prow, pcol, obj, searchpar)
        newfr.obsind = fitsfile.from_obsind
        newfrlist.append(newfr)
        newones += 1
    except find_results.FindResultErr as e:
        if verbose > 1:
            logging.write(e.args[0])
        notfound += 1

if notfound > 0  and  verbose > 0:
    logging.write(notfound, "objects not found")

if verbose > 0:
    logging.write("{:d} objects found".format(len(newfrlist)-1))

if len(newfrlist) < findmin:
    logging.die(60, "too few ({:d}) objects found need at least {:d}".format(len(newfrlist), findmin))

if deleteold and num_existing > 1:
    if verbose > 0:
        logging.write("Deleting {:d} old results".format(num_existing-1))
    for fr in findres.results():
        if not fr.istarget:
            fr.delete(dbcurs)

findres.resultlist = newfrlist
# print("Num existing = {:d} donealready = {:d} num in list = {:d}".format(num_existing, donealready, len(newfrlist)))
if newones != 0:
    findres.reorder()
    findres.relabel()
    findres.rekey()
    findres.savedb(dbcurs)
    if verbose > 0:
        logging.write("Save complete")
else:
    if verbose > 0:
        logging.write("Save omitted nothing new")