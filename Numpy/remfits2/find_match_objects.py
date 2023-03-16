#!  /usr/bin/env python3

"""Find objects in image"""

import argparse
import warnings
import sys
from multiprocessing import Pool
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
import remdefaults
import remfits
import find_results
import searchparam
import objdata
import logs

def run_find(objpixes):
    """For running multiprocessor"""

    obj, pixes = objpixes
    pcol, prow = pixes
    if  pcol < trimleft or prow < trimbottom or pcol >= maxcol or prow >= maxrow or obj.is_target():
        if verbose > 1:
            logging.write(obj.dispname, "not in image")
        return None
    try:
        newfr = findres.find_object(prow, pcol, obj, searchpar)
        newfr.obsind = fitsfile.from_obsind
        return newfr
    except find_results.FindResultErr as e:
        if verbose > 1:
            logging.write(e.args[0])
        return None

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
parsearg.add_argument('--maxproc', type=int, default=8, help='Maximum number of processes to run')
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
maxproc = resargs['maxproc']

# If we are saving stuff, do so and exit

if searchpar.saveparams:
    searchparam.save(searchpar)
    if verbose:
        searchpar.display(sys.stderr)
    sys.exit(0)

mydb, dbcurs = remdefaults.opendb(waitlock=True)

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

if num_existing > 1:
    if not deleteold:
        logging.die(18, "Already done, use --deleteold if needed")
    if verbose > 0:
        logging.write("Deleting {:d} old results".format(num_existing-1))
    for fr in findres.results():
        if not fr.istarget:
            fr.delete(dbcurs)

# Get objects in vicinity

objlist = objdata.get_sky_region(dbcurs, fitsfile, maxvar)
coordlist = [(obj.ra, obj.dec) for obj in objlist]
pixlist = fitsfile.wcs.coords_to_pix(coordlist)
maxrow = fitsfile.nrows - trimtop
maxcol = fitsfile.ncolumns - trimright

# Build new results list

newfrlist = [targfr]
notfound = newones = 0
objpixes = list(zip(objlist, pixlist))

while len(objpixes) != 0:
    seg = objpixes[:maxproc]
    objpixes = objpixes[maxproc:]
    with Pool(min(len(seg), maxproc)) as p:
        results = p.map(run_find, seg)
        for r in results:
            if r is None:
                notfound += 1
            else:
                newfrlist.append(r)
                newones += 1

if notfound > 0  and  verbose > 0:
    logging.write(notfound, "objects not found")

if verbose > 0:
    logging.write("{:d} objects found".format(newones))

if newones+1 < findmin:
    logging.die(60, "too few ({:d}) objects found need at least {:d}".format(len(newfrlist), findmin))

findres.resultlist = newfrlist
# print("Num existing = {:d} donealready = {:d} num in list = {:d}".format(num_existing, donealready, len(newfrlist)))
findres.reorder()
findres.relabel()
findres.rekey()
if verbose > 0:
    logging.write("About to start saving to DB")
findres.save_as_block(dbcurs)
if verbose > 0:
    logging.write("Save complete")
