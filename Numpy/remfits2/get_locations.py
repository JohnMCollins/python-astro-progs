#!  /usr/bin/env python3

from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
from astropy.io import fits
from astropy.time import Time
import datetime
import numpy as np
import argparse
import warnings
import sys
import miscutils
import math
import remdefaults
import remfits
import os.path
import obj_locations
import objdata
import wcscoord

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

parsearg = argparse.ArgumentParser(description='Get locations from database corresponding to image', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', nargs=2, type=str, help='Image file and output location file')
remdefaults.parseargs(parsearg, tempdir=False)
parsearg.add_argument('--force', action='store_true', help='Force overwrite of existing file')
parsearg.add_argument('--verbose', action='store_true', help='List details')

resargs = vars(parsearg.parse_args())
infile, outfile = resargs['files']
remdefaults.getargs(resargs)
force = resargs['force']
verbose = resargs['verbose']

mydb, dbcurs = remdefaults.opendb()

try:
    inputfile = remfits.parse_filearg(infile, dbcurs)
except remfits.RemFitsErr as e:
    print(e.args[0], file=sys.stderr)
    sys.exit(52)

if inputfile.target is None:
    print("No target found in", infile, file=sys.stderr)
    sys.exit(53)

try:
    objlist = objdata.get_objects(dbcurs, inputfile.target, inputfile.date)
except objdata.ObjDataError as e:
    print("Search gave error", e.args[0], e.args[1])
    sys.exit(54)

if verbose:
    print(len(objlist), "Possible objects prior to restriction to image", file=sys.stderr)

w = wcscoord.wcscoord(inputfile.hdr)
pixrows, pixcols = inputfile.data.shape
cornerpix = ((0, 0), (pixcols - 1, 0), (0, pixrows - 1), (pixcols - 1, pixrows - 1))
cornerradec = w.pix_to_coords(cornerpix)
ras = [c[0] for c in cornerradec]
decs = [c[1] for c in cornerradec]

objlist = objdata.prune_objects(objlist, ras, decs)

if verbose:
    print(len(objlist), "Possible objects after to restriction to image", file=sys.stderr)

if len(objlist) < 2:
    print("Not enough possible objects in list", file=sys.stderr)
    sys.exit(100)

objstr = obj_locations.ObjLocs(inputfile)
for obj in objlist:
    objstr.add_loc(obj)
objstr.get_offsets_in_image()

try:
    obj_locations.save_objlist_to_file(objstr, outfile, force)
except obj_locations.ObjLocErr as e:
    print(e.args[0], file=sys.stderr)
    sys.exit(100)
