#!  /usr/bin/env python3

import dbops
import remdefaults
import argparse
import sys
import os.path
import miscutils
import numpy as np
import remfits
import remget
import fitsops

parsearg = argparse.ArgumentParser(description='Gather tally of statistics from arbitrary fits files limited to filter and type', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('fitsids', nargs='+', type=int, help='List of FITS ids')
remdefaults.parseargs(parsearg, tempdir=False, inlib=False)
parsearg.add_argument('--outfile', required=True, type=str, help='Result file')
parsearg.add_argument('--force', action='store_true', help='OK to overwrite existing file')

resargs = vars(parsearg.parse_args())
fitsids = resargs['fitsids']
remdefaults.getargs(resargs)
force = resargs['force']
outfile = remdefaults.libfile(resargs['outfile'])

fitsdone = dict()
if os.path.exists(outfile) and not force:
    print("Output file", outfile, "already exists - aborting, use --force if needed", file=sys.stderr)
    sys.exit(11)

dbase, dbcurs = remdefaults.opendb()

firstone = fitsids.pop(0)
dbcurs.execute("SELECT nrows,ncols FROM fitsfile WHERE ind=%d" % firstone)
dbrows = dbcurs.fetchall()
if len(dbrows) <= 0:
    print("Fitsid", firstone, "not found", file=sys.stderr)
    sys.exit(12)

fitsdone[firstone] = 1
rows, cols = dbrows[0]
tally = np.zeros((3, rows, cols), dtype=np.float64)
try:
    ffmem = remget.get_saved_fits(dbcurs, firstone)
except remget.RemGetError as e:
    print("Could not fetch ind", fitsind, "error was", e.args[0], file=sys.stderr)

fhdr, fdat = fitsops.mem_get(ffmem)
try:
    fh = remfits.RemFitsHdr(fhdr)
    filter = fh.filter
    ftype = fh.ftype
except remfits.RemFitsErr as e:
    print("fitsid", firstone, "gave error", e.args[0], file=sys.stderr)
    sys.exit(13)

fdat = fdat[0:rows, 0:cols].astype(np.float64)
tally[0] += 1.0
tally[1] += fdat
tally[2] += fdat ** 2

for fid in fitsids:
    if fid in fitsdone:
        print("Already done", fid, file=sys.stderr)
        continue
    fitsdone[fid] = 1
    dbcurs.execute("SELECT nrows,ncols FROM fitsfile WHERE ind=%d" % fid)
    dbrows = dbcurs.fetchall()
    if len(dbrows) <= 0:
        print("Fitsid", fid, "not found", file=sys.stderr)
        continue
    nrows, ncols = dbrows[0]
    if nrows != rows or ncols != cols:
        print("First id", firstone, "is", rows, "by", cols, "but", fid, "is", nrows, "by", ncols, file=sys.stderr)
        continue
    try:
        ffmem = remget.get_saved_fits(dbcurs, fid)
    except remget.RemGetError as e:
        print("Could not fetch ind", fitsind, "error was", e.args[0], file=sys.stderr)
        continue

    fhdr, fdat = fitsops.mem_get(ffmem)
    try:
        fh = remfits.RemFitsHdr(fhdr)
        if fh.filter != filter:
            print(fid, "is filter", fh.filter, "expecting", filter, file=sys.stderr)
            continue
        if fh.ftype != ftype:
            print(fid, "is type", fh.ftype, "expecting", ftype, file=sys.stderr)
            continue
    except remfits.RemFitsErr as e:
        print("fitsid", fid, "gave error", e.args[0], file=sys.stderr)
        continue
    fdat = fdat[0:rows, 0:cols].astype(np.float64)
    tally[0] += 1.0
    tally[1] += fdat
    tally[2] += fdat ** 2

np.save(outfile, tally)
