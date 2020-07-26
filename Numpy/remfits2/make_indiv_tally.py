#!  /usr/bin/env python3

import dbops
import remdefaults
import argparse
import sys
import os.path
import dbremfitsobj
import miscutils
import numpy as np
import remfitshdr

parsearg = argparse.ArgumentParser(description='Gather tally of statistics from arbitrary fits filts limiter to filter and type', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('fitsids', nargs='+', type=int, help='List of FITS ids')
remdefaults.parseargs(parsearg, tempdir=False, inlib=False)
parsearg.add_argument('--outfile', required=True, type=str, help='Result file')
parsearg.add_argument('--force', action='store_true', help='OK to overwrite existing file')
parsearg.add_argument('--inlib', action='store_true', help='Load and store in library return than CWD by default')

resargs = vars(parsearg.parse_args())
fitsids = resargs['fitsids']
remdefaults.getargs(resargs)
force = resargs['force']
outfile = remdefaults.libfileresargs['outfile'])

fitsdone = dict()
if os.path.exists(outfile) and not force:
    print("Output file", outfile, "already exists - aborting, use --force if needed", file=sys.stderr)
    sys.exit(11)

dbase, dbcurs = remdefaults.opendb()

firstone = fitsids.pop(0)
dbcurs.execute("SELECT rows,cols FROM fitsfile WHERE ind=%d" % firstone)
dbrows = dbcurs.fetchall()
if len(dbrows) <= 0:
    print("Fitsid", firstone, "not found", file=sys.stderr)
    sys.exit(12)

fitsdone[firstone] = 1
rows, cols = dbrows[0]
tally = np.zeros((3, rows, cols), dtype=np.float64)
ff = dbremfitsobj.getfits(dbcurs, firstone)
try:
    fh = remfitshdr.RemFitsHdr(ff[0].header)
    filter = fh.filter
    ftype = fh.ftype
except remfitshdr.RemFitsHdrErr as e:
    print("fitsid", firstone, "gave error", e.args[0], file=sys.stderr)
    sys.exit(13)

fdat = ff[0].data[0:rows, 0:cols].astype(np.float64)
ff.close()
tally[0] += 1.0
tally[1] += fdat
tally[2] += fdat ** 2

for fid in fitsids:
    if fid in fitsdone:
        print("Already done", fid, file=sys.stderr)
        continue
    fitsdone[fid] = 1
    dbcurs.execute("SELECT rows,cols FROM fitsfile WHERE ind=%d" % fid)
    dbrows = dbcurs.fetchall()
    if len(dbrows) <= 0:
        print("Fitsid", fid, "not found", file=sys.stderr)
        continue
    nrows, ncols = dbrows[0]
    if nrows != rows or ncols != cols:
        print("First id", firstone, "is", rows, "by", cols, "but", fid, "is", nrows, "by", ncols, file=sys.stderr)
        continue
    ff = dbremfitsobj.getfits(dbcurs, fid)
    try:
        fh = remfitshdr.RemFitsHdr(ff[0].header)
        if fh.filter != filter:
            print(fid, "is filter", fh.filter, "expecting", filter, file=sys.stderr)
            continue
        if fh.ftype != ftype:
            print(fid, "is type", fh.ftype, "expecting", ftype, file=sys.stderr)
            continue
    except remfitshdr.RemFitsHdrErr as e:
        print("fitsid", fid, "gave error", e.args[0], file=sys.stderr)
        continue
    fdat = ff[0].data[0:rows, 0:cols].astype(np.float64)
    ff.close()
    tally[0] += 1.0
    tally[1] += fdat
    tally[2] += fdat ** 2

np.save(outfile, tally)
