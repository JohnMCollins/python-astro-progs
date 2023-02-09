#!  /usr/bin/env python3

"""Find target in image"""

import argparse
import warnings
import sys
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
import remdefaults
import remfits
import objdata
import find_results
import searchparam
import logs

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

searchpar = searchparam.load()
parsearg = argparse.ArgumentParser(description='Find target in image having listed possible objects', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('file', nargs=1, type=str, help='Image file')
searchpar.argparse(parsearg)
remdefaults.parseargs(parsearg, tempdir=False, inlib=False)
parsearg.add_argument('--updatedb', action='store_true', help='Update DB with offsets')
parsearg.add_argument('--verbose', action='store_true', help='Tell everything')
parsearg.add_argument('--force', action='store_true', help='Force if done already')
parsearg.add_argument('--filter', type=str, help='Ignore if not one of these filters')
parsearg.add_argument('--skylevelstd', type=float, default=remfits.DEFAULT_SKYLEVELSTD, help='Theshold level of std devs to include points in sky')
parsearg.add_argument('--replace', action='store_true', help='Replace all findresults for other objects')
logs.parseargs(parsearg)

resargs = vars(parsearg.parse_args())
infilename = resargs['file'][0]
remdefaults.getargs(resargs)
searchpar.getargs(resargs)
updatedb = resargs['updatedb']
verbose = resargs['verbose']
skylevstd = resargs['skylevelstd']
replaceprev = resargs['replace']
force = resargs['force']
filt = resargs['filter']
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
    fitsfile.calc_skylevel(skylevstd)
except remfits.RemFitsErr as e:
    logging.die(52, e.args[0])

if filt is not None and fitsfile.filter not in filt:
    logging.die(59, "filter is", fitsfile.filter, "not in specified", filt)

current_obsind = fitsfile.from_obsind

try:
    target_obj = objdata.ObjData()
    target_obj.get(dbcurs, name=fitsfile.target)
    target_obj.apply_motion(dbcurs, fitsfile.date)
except objdata.ObjDataError as e:
    logging.die(53, "Problem with target in file", e.args[0])

db_roff = db_coff = 0

if fitsfile.pixoff is None:
    fitsfile.pixoff = remfits.Pixoffsets(remfits=fitsfile)
elif  fitsfile.pixoff.coloffset is not None:
    db_roff = fitsfile.pixoff.rowoffset
    db_coff = fitsfile.pixoff.coloffset
    if verbose:
        logging.write("Existing database offsets r={:.4f} c={:.4f}".format(db_roff, db_coff))

targcol, targrow = fitsfile.wcs.coords_to_colrow(target_obj.ra, target_obj.dec)
if verbose:
    logging.write("Starting row {:.4f} col {:.4f}".format(targrow, targcol))

try:
    findres = find_results.FindResults(remfitsobj=fitsfile)
    if not replaceprev or not force:
        findres.loaddb(dbcurs)
        if not force and findres.num_results() != 0 and findres[0].obj.is_target():
            logging.die(30, "Target already found use --force if needed")
    fr = findres.find_object(targrow, targcol, target_obj, searchpar)
except find_results.FindResultErr as e:
    logging.die(10, "Could not find target", target_obj.dispname, "in image")

fr.obsind = current_obsind

dbchanges = 0
updoffs = False

if updatedb and (round(fr.rdiff,4) != 0 or round(fr.cdiff,4) != 0):
    fitsfile.pixoff.set_offsets(dbcurs, fr.rdiff, fr.cdiff)
    if verbose:
        logging.write("Updated offsets to r={:.4f} c={:.4f}".format(fitsfile.pixoff.rowoffset, fitsfile.pixoff.coloffset))
    dbchanges += 1
    updoffs = True

if replaceprev:
    dbchanges += dbcurs.execute("DELETE FROM findresult WHERE obsind={:d}".format(current_obsind))
    dbchanges += dbcurs.execute("DELETE FROM aducalc WHERE obsind={:d}".format(current_obsind))

findres.insert_result(fr)
dbchanges += 1

if updoffs:
    # Adjust offsets of all previous find results including one we just did.
    dbchanges += findres.adjust_offsets(dbcurs, -fr.rdiff, -fr.cdiff)

findres.reorder()
findres.relabel()
findres.rekey()

findres.savedb(dbcurs, replaceprev)

mydb.commit()
