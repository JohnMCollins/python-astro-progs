#!  /usr/bin/env python3

"""Apply fix zeros to aperatures
superseded"""

import argparse
import warnings
import sys
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
import remdefaults
import remfits
import obj_locations
import find_results
import searchparam
import logs

def fix_fr_aperture(fres, row, col, adus, aps):
    """Adjust aperture size and row/col in findresult"""
    fres.rdiff += row - fres.row
    fres.cdiff += col - fres.col
    fres.row = row
    fres.col = col
    fres.adus = adus
    fres.apsize = fres.obj.apsize = aps

# Shut up warning messages


warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

searchpar = searchparam.load()
parsearg = argparse.ArgumentParser(description='Find and fix zero aperatures in results', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('file', nargs=1, type=str, help='Image file')
parsearg.add_argument('--objloc', type=str, help='Name for object locations file if to be different from image file name')
parsearg.add_argument('--findres', type=str, help='Name for find results file if to be different from image file name')
searchpar.argparse(parsearg)
remdefaults.parseargs(parsearg, tempdir=False, inlib=False)
parsearg.add_argument('--updatedb', action='store_true', help='Update database')
parsearg.add_argument('--verbose', action='store_true', help='Tell everything')
logs.parseargs(parsearg)

resargs = vars(parsearg.parse_args())
infilename = resargs['file'][0]
objlocprefix = resargs['objloc']
findresprefix = resargs['findres']
remdefaults.getargs(resargs)
searchpar.getargs(resargs)
verbose = resargs['verbose']
updatedb = resargs['updatedb']
logging = logs.getargs(resargs)

logging.die(200, "This program has been superseded now find result are stored in the database")

# If we are saving stuff, do so and do not exit

if searchpar.saveparams:
    searchparam.save(searchpar)
    if verbose:
        searchpar.display(sys.stderr)

mydb, dbcurs = remdefaults.opendb()

try:
    fitsfile = remfits.parse_filearg(infilename, dbcurs)
except remfits.RemFitsErr as e:
    logging.die(52, e.args[0])

if objlocprefix is None:
    if infilename.isdigit():
        logging.die(10, "Need to give objloc file name when image file", infilename, "given as digits")
    objlocprefix = infilename

if findresprefix is None:
    if infilename.isdigit():
        logging.die(11, "Need to give find results file name when image file", infilename, "given as digits")
    findresprefix = infilename

# Now open all the files

try:
    objlocfile = obj_locations.load_objlist_from_file(objlocprefix, fitsfile)
except obj_locations.ObjLocErr as e:
    logging.die(12, "Unable to load objloc file, error was", e.args[0])

if objlocfile.num_results() == 0:
    logging.die(13, "No results in objloc file", objlocprefix)

try:
    findres = find_results.load_results_from_file(findresprefix, fitsfile)
except find_results.FindResultErr as e:
    logging.die(14, "Unable to load findres file, error was", e.args[0])

frchanges = dbchanges = errors = 0

for fr in findres.results(idonly=True, nohidden=True):
    if not fr.hide and fr.apsize == 0 or fr.obj.apsize == 0:
        oapp = findres.opt_aperture(fr.row, fr.col, searchpar)
        if oapp is None:
            logging.write("Could not find object near r={:d} c={:d}".format(fr.row, fr.col))
            errors += 1
            continue
        aperture, trow, tcol, tadus = oapp
        if verbose:
            logging.write("Assigning size of", aperture, "to", fr.obj.dispname)
        fix_fr_aperture(fr, trow, tcol, tadus, aperture)
        frchanges += 1
        if updatedb and fr.obj.objind != 0:
            dbch = dbcurs.execute("UPDATE objdata SET apsize={:d} WHERE ind={:d}".format(aperture, fr.obj.objind))
            if dbch != 0:
                dbchanges += dbch
                if verbose:
                    logging.write("Database change to aperture {:d} for {:s}".format(aperture, fr.obj.dispname))
            elif verbose:
                logging.write("No changes for aperture on {:s}".format(fr.obj.dispname))

if errors > 0:
    logging.die(50, "Aborting due to", errors, "errors")

if frchanges != 0:
    findres.reorder()
    findres.relabel()
    find_results.save_results_to_file(findres, findresprefix, force=True)
    if verbose:
        logging.write(frchanges, "changes to findres file")
if dbchanges != 0:
    mydb.commit()
    if verbose:
        logging.write(dbchanges, "changes to database")

if frchanges + dbchanges == 0:
    sys.exit(1)
sys.exit(0)
