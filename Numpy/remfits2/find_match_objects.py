#!  /usr/bin/env python3

"""Find objects in image"""

import argparse
import warnings
import sys
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
import remdefaults
import remfits
import obj_locations
import find_results

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

parsearg = argparse.ArgumentParser(description='Find objects in image after finding target', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('file', nargs=1, type=str, help='Image file and output find results')
parsearg.add_argument('--objloc', type=str, help='Name for object locations file if to be different from image file name')
parsearg.add_argument('--findres', type=str, help='Name for find results file if to be different from image file name')
remdefaults.parseargs(parsearg, tempdir=False, inlib=False)
parsearg.add_argument('--force', action='store_true', help='Force overwrite of existing file if targets found already')
parsearg.add_argument('--apsize', type=int, default=6, help='Aperature size to use if none assigned')
parsearg.add_argument('--signif', type=float, default=find_results.DEFAULT_SIGN / 10.0, help='No of std devs above sky to be significant')
parsearg.add_argument('--totsign', type=float, default=find_results.DEFAULT_TOTSIGN, help='Total significance')
parsearg.add_argument('--maxshift', type=int, default=3, help='Maximum pixel displacement looking for objects')
parsearg.add_argument('--minbri', type=float, default=5, help='Minimum brightness of objects as percentage of target')
parsearg.add_argument('--nogaia', action='store_true', help='Omit listing GAIA objects')
parsearg.add_argument('--verbose', action='store_true', help='Tell everything')
parsearg.add_argument('--findmin', type=int, default=10, help='Minimum number to find to consider success')

resargs = vars(parsearg.parse_args())
infilename = resargs['file'][0]
remdefaults.getargs(resargs)
force = resargs['force']
findresprefix = resargs['findres']
objlocprefix = resargs['objloc']
apsize = resargs['apsize']
signif = resargs['signif']
totsign = resargs['totsign']
maxshift = resargs['maxshift']
minbri = resargs['minbri']
nogaia = resargs['nogaia']
verbose = resargs['verbose']
findmin = resargs['findmin']

mydb, dbcurs = remdefaults.opendb()

try:
    fitsfile = remfits.parse_filearg(infilename, dbcurs)
except remfits.RemFitsErr as e:
    print(e.args[0], file=sys.stderr)
    sys.exit(52)

if objlocprefix is None:
    if infilename.isdigit():
        print("Need to give objloc file name when image file from DB", infilename, "given as digits", file=sys.stderr)
        sys.exit(10)
    objlocprefix = infilename

if findresprefix is None:
    if infilename.isdigit():
        print("Need to give find results file name when image file from DB", infilename, "given as digits", file=sys.stderr)
        sys.exit(11)
    findresprefix = infilename

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
    print("Could not open findres file, error was", e.args[0])
    sys.exit(14)

if findres.num_results() != 1:
    if findres.num_results() == 0:
        print("No results in findres file, expecting at least 1 for target", file=sys.stderr)
        sys.exit(15)
    if not force:
        print("{:d} objects found already, use --force if needed".format(findres.num_results()), file=sys.stderr)
        sys.exit(16)

targfr = findres[0]

if not targfr.istarget:
    print("No target (should be first) in findres file", file=sys.stderr)
    sys.exit(17)

db_roff = db_coff = 0

if fitsfile.pixoff is not None and fitsfile.pixoff.coloffset is not None:
    db_roff = fitsfile.pixoff.rowoffset
    db_coff = fitsfile.pixoff.coloffset
    if verbose:
        print("Using database offsets r={:d} c={:d}".format(db_roff, db_coff))

# Accumulate new results list
# If we have row and column diffs in the target, use that so we look relative to that

erowoffset = targfr.rdiff
ecoloffset = targfr.cdiff

newresults = [ targfr ]

found = 0

for ol in objlocfile.results():
    if ol.istarget:
        continue
    aps = ol.apsize
    msg = "*"
    if aps == 0:
        aps = apsize
        msg = "(def)"

    offs = findres.find_object(ol, maxshift=maxshift, signif=signif, totsign=totsign, defapwidth=aps, eoffrow=erowoffset, eoffcol=ecoloffset)
    if offs is None:
        if verbose:
            print("Could not find", ol.dispname, "ap", aps, msg, file=sys.stderr)
        continue

    offr, offc, row, col, adus = offs[0]
    fr = find_results.FindResult(row=row,
                                 col=col,
                                 apsize=ol.apsize,
                                 adus=adus,
                                 rdiff=offr + erowoffset,
                                 cdiff=offc + ecoloffset,
                                 obj=ol)
    newresults.append(fr)
    found += 1

if found < findmin:
    print("Not enough objects found, looking for", findmin, "only found", found, file=sys.stderr)
    sys.exit(1)

findres.resultlist = newresults
findres.calccoords()
findres.reorder()
findres.relabel()
findres.rekey()

try:
    find_results.save_results_to_file(findres, findresprefix, force=True)
except find_results.FindResultErr as e:
    print(e.args[0], file=sys.stderr)
    sys.exit(100)
