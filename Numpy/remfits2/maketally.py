#!  /usr/bin/env python3

import dbops
import remdefaults
import argparse
import sys
import os.path
import miscutils
import numpy as np
import parsetime
import remfield
import remget
import fitsops

parsearg = argparse.ArgumentParser(description='Gather tally of statistics for CCD array', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg, tempdir=False)
parsetime.parseargs_daterange(parsearg)
remfield.parseargs(parsearg)
parsearg.add_argument('--type', type=str, default='obs', choices=('obs', 'flat', 'bias'), help='What kind of file tp process#')
parsearg.add_argument('--create', action='store_true', help='Expecting to create file rather than append to existing file')
parsearg.add_argument('--prefix', required=True, type=str, help='Result file prefix')

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
create = resargs['create']
prefix = resargs['prefix']
ftype = resargs['type']
fieldselect = []
try:
    parsetime.getargs_daterange(resargs, fieldselect)
except ValueError as e:
    print(e.args[0], file=sys.stderr)
    sys.exit(20)

try:
    remfield.getargs(resargs, fieldselect)
except remfield.RemFieldError as e:
    print(e.args[0], file=sys.stderr)
    sys.exit(21)

fitsidfn = remdefaults.fitsid_file(prefix)
tallyfn = remdefaults.tally_file(prefix)

fitsids = dict()

if create:
    if os.path.exists(fitsidfn):
        print("FITS id file", fitsidfn, "already exists - aborting", file=sys.stderr)
        sys.exit(10)
    if os.path.exists(tallyfn):
        print("FITS tally file", tallyfn, "already exists - aborting", file=sys.stderr)
        sys.exit(11)
    tally = np.zeros((3, 2048, 2048), dtype=np.float64)
else:
    try:
        tally = np.load(tallyfn)
        with open(fitsidfn, 'rt') as fidf:
            for l in fidf:
                dict[int(l)] = 1
    except OSError as e:
        print("Cannot open", e.filename, "error was", e.args[1], file=sys.stderr)
        sys.exit(12)

dbase, dbcurs = remdefaults.opendb()
fieldselect.append("gain=1")
fieldselect.append("nrows IS NOT NULL")
fieldselect.append("rejreason IS NULL")

if ftype == 'obs':
    tab = "obsinf"
else:
    fieldselect.append("typ='" + ftype + "'")
    tab = "iforbinf"

dbcurs.execute("SELECT ind,nrows,ncols,startx,starty FROM " + tab + " WHERE " + " AND ".join(fieldselect))
dbrows = dbcurs.fetchall()
for dbrow in dbrows:
    fitsind, rows, cols, startx, starty = dbrow
    if fitsind in fitsids:
        continue
    fitsids[fitsind] = 1
    try:
        ffmem = remget.get_saved_fits(dbcurs, fitsind)
    except remget.RemGetError as e:
        print("Could not fetch ind", fitsind, "error was", e.args[0], file=sys.stderr)
        continue

    ffhdr, fdat = fitsops.mem_get(ffmem)
    fdat = fdat[0:rows, 0:cols]
    fdat = fdat.astype(np.float64)
    endr = starty + rows
    endc = startx + cols
    try:
        tally[0, starty:endr, startx:endc] += 1.0
        tally[1, starty:endr, startx:endc] += fdat
        tally[2, starty:endr, startx:endc] += fdat ** 2
    except ValueError:
        print("Wrong size ind = ", fitsind, "r/c/sx/sy", rows, cols, startx, starty, file=sys.stderr)

outf = open(fitsidfn, 'wt')
for k in sorted(fitsids.keys()):
    print(k, file=outf)
outf.close()

outf = open(tallyfn, "wb")
np.save(outf, tally)
outf.close()
