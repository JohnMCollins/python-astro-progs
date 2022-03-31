#!  /usr/bin/env python3

"""Find target in image"""

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

parsearg = argparse.ArgumentParser(description='Find target in image having listed possible objects', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('file', nargs=1, type=str, help='Image file and output find results')
parsearg.add_argument('--objloc', type=str, help='Name for object locations file if to be different from image file name')
parsearg.add_argument('--findres', type=str, help='Name for find results file if to be different from image file name')
remdefaults.parseargs(parsearg, tempdir=False, inlib=False)
parsearg.add_argument('--force', action='store_true', help='Force overwrite of existing file')
parsearg.add_argument('--apsize', type=int, default=6, help='Aperature size to use if none assigned')
parsearg.add_argument('--signif', type=float, default=find_results.DEFAULT_SIGN, help='No of std devs above sky level to start search')
parsearg.add_argument('--totsign', type=float, default=find_results.DEFAULT_TOTSIGN, help='Total significance')
parsearg.add_argument('--maxshift', type=int, default=7, help='Maximum pixel displacement looking for objects first pass')
parsearg.add_argument('--updatedb', action='store_true', help='Update DB with offsets')
parsearg.add_argument('--locupdate', action='store_true', help='Update objloc file with offsets')
parsearg.add_argument('--verbose', action='store_true', help='Tell everything')
parsearg.add_argument('--listbest', type=int, default=0, help='List n best solutions')

resargs = vars(parsearg.parse_args())
infilename = resargs['file'][0]
remdefaults.getargs(resargs)
force = resargs['force']
findresprefix = resargs['findres']
objlocprefix = resargs['objloc']
defapsize = resargs['apsize']
signif = resargs['signif']
totsign = resargs['totsign']
maxshift = resargs['maxshift']
updatedb = resargs['updatedb']
locupdate = resargs['locupdate']
verbose = resargs['verbose']
listbest = resargs['listbest']

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

try:
    objlocfile = obj_locations.load_objlist_from_file(objlocprefix, fitsfile)
except obj_locations.ObjLocErr as e:
    print("Unable to load objloc file, error was", e.args[0], file=sys.stderr)
    sys.exit(12)

if objlocfile.num_results() == 0:
    print("No results in objloc file", objlocprefix, file=sys.stderr)
    sys.exit(13)

existing_target = None
try:
    findres = find_results.load_results_from_file(findresprefix, fitsobj=fitsfile, oknotfound=True)
    if findres.num_results() != 0 and findres[0].istarget:
        if  not force:
            print("Looks like target found already, use --force if needed", file=sys.stderr)
            sys.exit(14)
        existing_target = findres[0]
except FileNotFoundError:
    findres = find_results.FindResults(fitsfile)
except find_results.FindResultErr as e:
    print("Error loading existing findres file", e.args[0], file=sys.stderr)
    sys.exit(15)

objloctarget = None
for ol in objlocfile.results():
    if ol.istarget:
        objloctarget = ol
        break

if objloctarget is None:
    print("Could not find a target in objloc file", objlocprefix, file=sys.stderr)
    sys.exit(16)

existing_roff = existing_coff = db_roff = db_coff = 0

if existing_target is not None:
    existing_roff = existing_target.rdiff
    existing_coff = existing_target.cdiff
    if verbose:
        print("Using existing target offsets r={:d} c={:d}".format(existing_roff, existing_coff))

if fitsfile.pixoff is None:
    fitsfile.pixoff = remfits.Pixoffsets(remfits=fitsfile)
elif  fitsfile.pixoff.coloffset is not None:
    db_roff = fitsfile.pixoff.rowoffset
    db_coff = fitsfile.pixoff.coloffset
    if verbose:
        print("Using database offsets r={:d} c={:d}".format(db_roff, db_coff))

offs = findres.find_object(objloctarget, eoffrow=existing_roff, eoffcol=existing_coff, maxshift=maxshift, signif=signif, totsign=totsign, defapwidth=defapsize)

# NB Exit code of 1 if we didn't find the targe

if offs is None:
    print("Could not find target", objloctarget.dispname, "in image", infilename, file=sys.stderr)
    sys.exit(1)

if listbest > 0:
    n = 0
    try:
        print("Rdf,Cdf  Row, Col        ADUs       %")
        tperc = offs[0][-1] / 100.0
        for rowoffset, coloffset, row, column, adus in offs:
            print("{:3d},{:3d} {:4d},{:4d}: {:10.2f} {:7.2f}".format(rowoffset - existing_roff - db_roff, coloffset - existing_coff - db_coff, row, column, adus, adus / tperc))
            n += 1
            if n >= listbest:
                break
        if existing_coff != 0 or existing_roff != 0:
            print("\nOffsets are in addition to existing offsets of {:d},{:d}".format(existing_roff, existing_coff))
    except (KeyboardInterrupt, BrokenPipeError):
        pass

# Taking first match (find_object returns results in descending ADU order)

rowoffset, coloffset, row, column, adus = offs[0]
rowoffset += existing_roff
coloffset += existing_coff

targ_findresult = find_results.FindResult(adus=adus,
                                          label="A",
                                          col=objloctarget.col,
                                          row=objloctarget.row,
                                          apsize=objloctarget.apsize,
                                          radeg=objloctarget.ra,
                                          decdeg=objloctarget.dec,
                                          obj=objloctarget)
targ_findresult.istarget = True

if updatedb:
    # Get any existing offset in database first as new offset is on top
    # Take account that the row and cols we have in the objloc are net of the existing one if any
    rowoffset -= db_roff
    coloffset -= db_coff
    if coloffset != 0  or  rowoffset != 0:
        if verbose:
            print("Setting col offset to {:d} row offset to {:d}".format(coloffset, rowoffset), file=sys.stderr)
        fitsfile.pixoff.set_offsets(dbcurs, rowoffset=rowoffset, coloffset=coloffset)
        mydb.commit()
        # We don't fiddle with row or column as we've just fixed them to line up
        # Don't need to set rdiff and cdiff to zero in targ_findresult as the init routine did it for us
elif rowoffset != 0  or  coloffset != 0:
    targ_findresult.col = column
    targ_findresult.row = row
    if locupdate:
        # If we are undating the objloc file we adjust all the row and columns in the objloc file by
        # the offsets we found
        replol = []
        pixrows, pixcols = fitsfile.data.shape
        for ol in objlocfile.results():
            ol.row += rowoffset
            ol.col += coloffset
            if ol.row >= 0 and ol.col >= 0 and ol.row < pixrows and ol.col < pixcols:
                replol.append(ol)
        objlocfile.resultlist = replol
        obj_locations.save_objlist_to_file(objlocfile, objlocprefix, force=True)
        # targ_findresult.cdiff = targ_findresult.rdiff = 0 done already in init
    else:
        # Not updating anything, set row and column and differences to what we found
        targ_findresult.radeg, targ_findresult.decdeg = fitsfile.wcs.colrow_to_coords(column, row)
        targ_findresult.cdiff = coloffset - db_coff
        targ_findresult.rdiff = rowoffset - db_roff

findres.resultlist = [targ_findresult]
try:
    find_results.save_results_to_file(findres, findresprefix, force=True)
except find_results.FindResultErr as e:
    print("Save of results gave error:", e.args[0], file=sys.stderr)
    sys.exit(2)
