#!  /usr/bin/env python3

"""Naje takkt file from FITS files"""

import argparse
import sys
import warnings
import os.path
import numpy as np
import remdefaults
import col_from_file
import remfits
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
parsearg.add_argument('--clear', action='store_true', help='Clear contents of existing file')
parsearg.add_argument('--prefix', required=True, type=str, help='Result file prefix')
parsearg.add_argument('--trim', type=int, default=0, help='Amount to trim each edge of image')

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
files = resargs['files']
create = resargs['create']
prefix = resargs['prefix']
ftype = resargs['type']
clear = resargs['clear']
trim = resargs['trim']

gtype = None
if ftype == 'flat':
    gtype = 'F'
elif ftype == 'bias':
    gtype = 'B'

if len(files) == 0:
    files = col_from_file.col_from_file(sys.stdin, resargs['colnum'])

tallyfn = remdefaults.tally_file(prefix)
tally = None

if create:
    if clear or not os.path.exists(tallyfn):
        tally = np.concatenate((np.zeros((3, 2048, 2048), dtype=np.float64),
                                np.full((1, 2048, 2048), 1e60, dtype=np.float64),
                                np.full((1, 2048, 2048), -1e60, dtype=np.float64)), axis=0)
if tally is None:
    if not os.path.exists(tallyfn):
        print(tallyfn, "does not exist, use --create if needed (or specify libdir)", file=sys.stderr)
        sys.exit(11)
    try:
        tally = np.load(tallyfn)
    except OSError as e:
        print("Cannot open", e.filename, "error was", e.args[1], file=sys.stderr)
        sys.exit(12)

if tally.shape != (5, 2048, 2048):
    print("Unexpected tally shape in", tallyfn, "Expected (5,2048,2048) found", tally.shape, file=sys.stderr)
    sys.exit(13)

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

with open(tallyfn, "wb") as outf:
    np.save(outf, tally)
