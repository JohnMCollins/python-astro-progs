#!  /usr/bin/env python3

"""Go through findresults files (with parallel image) and assign appertures where apsize is zero"""

import argparse
import warnings
import sys
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
import numpy as np
import remdefaults
import remfits
import find_results
import searchparam


class ApzRef:
    """Reference to ap zero object"""

    def __init__(self, filename, findres):
        self.filename = filename
        self.findres = findres
        self.adj = None


class ApzObject:
    """Record details of object with aperture zero"""

    def __init__(self, objname, ind):
        self.objname = objname
        self.objind = ind
        self.reflist = []
        self.basedon = self.meanap = self.apstd = None

    def addref(self, nref):
        """Add a reference to an ApzRef object"""
        self.reflist.append(nref)


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
parsearg = argparse.ArgumentParser(description='Find and assign zero apertures in resutlts', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', nargs='+', type=str, help='File names')
searchpar.argparse(parsearg)
remdefaults.parseargs(parsearg, tempdir=False, inlib=False)
parsearg.add_argument('--verbose', action='store_true', help='Tell everything')

resargs = vars(parsearg.parse_args())
files = resargs['files']
remdefaults.getargs(resargs)
searchpar.getargs(resargs)
verbose = resargs['verbose']

# If we are saving stuff, do so and do not exit

if searchpar.saveparams:
    searchparam.save(searchpar)
    if verbose:
        searchpar.display(sys.stderr)

mydb, dbcurs = remdefaults.opendb()

errors = 0
refs_by_ind = dict()
checkap_size = set()

# First pass to list zero size apertures by file

for file in files:

    try:
        fitsfile = remfits.parse_filearg(file, dbcurs)
    except remfits.RemFitsErr as e:
        print("Unable to open filts file, error was", e.args[0], file=sys.stderr)
        errors += 1
        continue

    try:
        frfile = find_results.load_results_from_file(file, fitsfile)
    except find_results.FindResultErr as e:
        print("Unable to load findres file, error was", e.args[0], file=sys.stderr)
        errors += 1
        continue

    for fr in frfile.results(idonly=True):
        if fr.apsize != 0:
            continue

        objind = fr.obj.objind
        try:
            reflist = refs_by_ind[objind]
        except KeyError:
            reflist = refs_by_ind[objind] = ApzObject(fr.obj.objname, objind)

        reflist.addref(ApzRef(file, frfile))
        if objind in checkap_size:
            continue
        dbcurs.execute("SELECT apsize FROM objdata WHERE ind={:d}".format(fr.obj.objind))
        zl = dbcurs.fetchall()
        if len(zl) != 1:
            print("Could not find object {:s} with ind {:d}".format(fr.obj.dispname, fr.obj.objind), file=sys.stderr)
            sys.exit(11)
        if zl[0][0] != 0:
            print("Expected aperture for {:s} to be zero not {:.2f} has this been run once".format(fr.obj.dispname, zl[0][0]))
            sys.exit(12)
        checkap_size.add(fr.obj.objind)

if errors != 0:
    print("Aborting due to failure to load", errors, "files", file=sys.stderr)
    sys.exit(10)

if len(refs_by_ind) == 0:
    print("Did not find any zero apertures", file=sys.stderr)
    sys.exit(1)

# OK for each one listed, generate the optimal apertures

rerrors = 0

for afr in refs_by_ind.values():
    if verbose:
        print("Calculing apertures for", afr.objname, "with", len(afr.reflist), "references", end='', file=sys.stderr)

    for ref in afr.reflist:
        fr = ref.findres[afr.objname]
        adj = ref.findres.opt_aperture(fr.row, fr.col, searchpar)
        if adj is None:
            print("Could not re-find aperture for", afr.objname, "in file", ref.filename, file=sys.stderr)
            rerrors += 1
            continue
        ref.adj = adj
    if rerrors != 0:
        errors += rerrors
        rerrors = 0  # Continue checking rest
        continue

    # Get list of apertures

    aperture_list = np.array([a.adj[0] for a in afr.reflist])
    if aperture_list.size == 0:
        print("Aperture list size=0? for", afr.objname, file=sys.stderr)
        errors += 1
        continue
    afr.basedon = aperture_list.size
    afr.meanap = round(aperture_list.mean(), 2)
    if aperture_list.size <= 1:
        if verbose:
            print(" apsize as {:.2f} based on {:d} values".format(afr.meanap, afr.basedon), file=sys.stderr)
    else:
        afr.apstd = round(aperture_list.std(), 2)
        if verbose:
            print(" apsize as {:.2f} std {:.2f} based on {:d} values".format(afr.meanap, afr.apstd, afr.basedon), file=sys.stderr)

if errors > 0:
    print("Aborting due to", errors, "errors", file=sys.stderr)
    sys.exit(30)

# Update findrefs where we have them
# Update database

for afr in refs_by_ind.values():

    for ref in afr.reflist:

        fr = ref.findres[afr.objname]
        dummy, trow, tcol, tadus = ref.adj  # We're using the mean ap size not the one for this ref
        fix_fr_aperture(fr, trow, tcol, tadus, afr.meanap)  # The adus won't be accurate as it's for the wrong aperture

    if afr.basedon == 1:
        query = "UPDATE objdata SET basedon=1,apstd=NULL,apsize={:.3f} WHERE ind={:d}".format(afr.meanap, afr.objind)
    else:
        query = "UPDATE objdata SET basedon={:d},apstd={:.3f},apsize={:.3f} WHERE ind={:d}".format(afr.basedon, afr.apstd, afr.meanap, afr.objind)

    dbcurs.execute(query)

mydb.commit()

# Finally update findref files avoiding doing them more than once

files_done = set()

for afr in refs_by_ind.values():

    for ref in afr.reflist:

        if ref.filename in files_done:
            continue

        ref.findres.reorder()
        ref.findres.relabel()
        # ref.findres.rekey() isn't needed I don't think

        try:
            find_results.save_results_to_file(ref.findres, ref.filename, force=True)
        except find_results.FindResultErr as e:
            print("Problem saving findres file", ref.findres, e.args[0], file=sys.stderr)
            errors += 1

        files_done.add(ref.filename)

if errors != 0:
    print(errors, "errors detected", file=sys.stderr)
    sys.exit(40)
