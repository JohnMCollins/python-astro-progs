#! /usr/bin/env python3

"""Track orientation of FITS Image files"""

import sys
import warnings
import argparse
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
import astroquery.utils as autils
import remdefaults
import remfits
import col_from_file
import wcscoord
import mydateutil

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)
autils.suppress_vo_warnings()

parsearg = argparse.ArgumentParser(description='Track orientation of FITS image files', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg, tempdir=False, libdir=False)
parsearg.add_argument('files', type=str, nargs='*', help='File names/IDs to display otherwise use id/file list from standard input')
parsearg.add_argument('--colnum', type=int, default=0, help='Column number to take from standard input')
parsearg.add_argument('--update', action="store_true", help='Update database with orientation')

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)

files = resargs['files']
if len(files) == 0:
    files = col_from_file.col_from_file(sys.stdin, resargs['colnum'])

update = resargs['update']

db, dbcurs = remdefaults.opendb()

counts = dict()
for c in (0, 90, 180, 270):
    counts[c] = 0

updates = 0

for file in files:

    try:
        ff = remfits.parse_filearg(file, dbcurs)
    except remfits.RemFitsErr as e:
        print(file, "open error", e.args[0], file=sys.stderr)
        continue

    w = wcscoord.wcscoord(ff.hdr)
    pixrows, pixcols = ff.data.shape
    cornerpix = ((0, 0), (pixcols - 1, pixrows - 1))
    ((blra, bldec), (trra, trdec)) = w.pix_to_coords(cornerpix)

    if trra < blra:
        if trdec > bldec:
            orient = 0
        else:
            orient = 1
    else:
        if trdec > bldec:
            orient = 3
        else:
            orient = 2
    rot = orient * 90
    print(file, "target", ff.target, "date", mydateutil.mysql_datetime(ff.date), "is rotated by", rot, "deg")
    counts[rot] += 1
    if update and ff.from_obsind != 0:
        dbcurs.execute("UPDATE obsinf SET orient={:d} WHERE obsind={:d}".format(orient, ff.from_obsind))
        updates += 1

if updates > 0:
    db.commit()

for c in (0, 90, 180, 270):
    print("{:3d}: {:5d}".format(c, counts[c]))
