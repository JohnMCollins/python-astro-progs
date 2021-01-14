#!  /usr/bin/env python3

import dbops
import remdefaults
import argparse
import sys
import os.path
import miscutils
import numpy as np
import col_from_file
import remfits
import warnings
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)
warnings.simplefilter('error', RuntimeWarning)  # Want div by zero etc to retunr error

parsearg = argparse.ArgumentParser(description='Gather tally of statistics for CCD array', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', nargs='*', type=str, help='Filenames or iforbinds to process, otherwise use stdin')
parsearg.add_argument('--colnum', type=int, default=0, help='Column to use from stdin')
remdefaults.parseargs(parsearg, tempdir=False)
parsearg.add_argument('--type', type=str, default='obs', choices=('obs', 'flat', 'bias'), help='What kind of file tp process')
parsearg.add_argument('--create', action='store_true', help='Expecting to create file rather than append to existing file')
parsearg.add_argument('--force', action='store_true', help='Force create new file on top of existing')
parsearg.add_argument('--prefix', required=True, type=str, help='Result file prefix')
parsearg.add_argument('--trim', type=int, default=0, help='Amount to trim each edge of image')

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
files = resargs['files']
create = resargs['create']
prefix = resargs['prefix']
ftype = resargs['type']
force = resargs['force']
trim = resargs['trim']

gtype = None
if ftype == 'flat':
    gtype = 'F'
elif ftype == 'bias':
    gtype = 'B'

if len(files) == 0:
    files = col_from_file.col_from_file(sys.stdin, resargs['colnum'])

tallyfn = remdefaults.tally_file(prefix)

if create:
    if not force:
        if os.path.exists(tallyfn):
            print("FITS tally file", tallyfn, "already exists - aborting use --force if needed", file=sys.stderr)
            sys.exit(11)
    tally = np.concatenate((np.zeros((3, 2048, 2048), dtype=np.float64), np.full((1, 2048, 2048), 1e60, dtype=np.float64), np.full((1, 2048, 2048), -1e60, dtype=np.float64)), axis=0)
else:
    try:
        tally = np.load(tallyfn)
    except OSError as e:
        print("Cannot open", e.filename, "error was", e.args[1], file=sys.stderr)
        sys.exit(12)

dbase, dbcurs = remdefaults.opendb()

for file in files:
    try:
        ff = remfits.parse_filearg(file, dbcurs, gtype)
    except remfits.RemFitsErr as e:
        print("Could not fetch file", file, "error was", e.args[0], file=sys.stderr)
        continue

    fdat = ff.data
    if trim != 0:
        fdat = fdat[trim:-trim, trim:-trim]
    startx = ff.startx + trim
    starty = ff.starty + trim
    endr = ff.endy - trim
    endc = ff.endx - trim

    try:
        tally[0, starty:endr, startx:endc] += 1.0
        tally[1, starty:endr, startx:endc] += fdat
        tally[2, starty:endr, startx:endc] += fdat ** 2
        tally[3, starty:endr, startx:endc] = np.minimum(tally[3, starty:endr, startx:endc], fdat)
        tally[4, starty:endr, startx:endc] = np.maximum(tally[4, starty:endr, startx:endc], fdat)
    except ValueError:
        print("Wrong size file = ", file, "r/c/sx/sy", endr - starty, endc - startx, startx, starty, file=sys.stderr)

outf = open(tallyfn, "wb")
np.save(outf, tally)
outf.close()
