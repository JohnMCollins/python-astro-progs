#! /usr/bin/env python3

# @Author: John M Collins <jmc>
# @Date:   2018-08-23T14:20:00+01:00
# @Email:  jmc@toad.me.uk
# @Filename: dbobjdisp.py
# @Last modified by:   jmc
# @Last modified time: 2019-01-04T23:02:43+00:00

from astropy.io import fits
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
import astroquery.utils as autils
import numpy as np
import argparse
import sys
import datetime
import os.path
import fcntl
import warnings
import miscutils
import remdefaults
import remget
import remfits
import fitsops
import col_from_file
import find_results

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)
autils.suppress_vo_warnings()

parsearg = argparse.ArgumentParser(description='Read observation or daily flat files and make counts of negative pixels with given bias', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg, tempdir=False)
parsearg.add_argument('files', type=str, nargs='*', help='File names/IDs to process otherwise take ids from standard input')
parsearg.add_argument('--colnum', type=int, default=0, help='Column number to take from standard input')
parsearg.add_argument('--countfile', type=str, required=True, help='Result file name')
parsearg.add_argument('--biasfile', type=str, help='Bias file name or ID')
parsearg.add_argument('--create', action='store_true', help='Create file, otherwise update existing file')
parsearg.add_argument('--force', action='store_true', help='Force create if file exists')
parsearg.add_argument('--igngeom', action='store_true', help='Ignore geometry differences between bias and obs/flat files, use common area')
parsearg.add_argument('--type', type=str, help='Put F or B here to select daily flat or bias for numerics')
parsearg.add_argument('--trim', type=int, default=0, help='Amount to trim off each edge')
parsearg.add_argument('--description', type=str, default='(no descr)', help='Description of what doing')

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)

countfile = remdefaults.count_file(resargs['countfile'])
create = resargs['create']
force = resargs['force']
igngeom = resargs['igngeom']
biasfile = resargs['biasfile']
typef = resargs['type']
trimsize = resargs['trim']
description = resargs['description']

countresult = np.zeros((2048, 2048), dtype=np.int32)

if create:
    if os.path.exists(countfile) and not force:
        print("Count file", countfile, "already exists, use --force if needed", file=sys.stderr)
        sys.exit(10)
    outf = open(countfile, 'wb')
    outf.truncate(0)
    np.save(outf, countresult)
    outf.close()
    sys.exit(0)

if not os.path.exists(countfile):
    print("Count file", countfile, "does not exist, use --create if needed first", file=sys.stderr)
    sys.exit(11)

files = resargs['files']
if len(files) == 0:
    files = col_from_file.col_from_file(sys.stdin, resargs['colnum'])

if biasfile is None:
    print("You need to specify a bias file if not creating", file=sys.stderr)
    sys.exit(12)

existresult = np.load(countfile)
if existresult.shape != (2048, 2048):
    print("Expecting", countfile, "to have shape 2048 x 2048 not", existresult.shape[0], "x", existresult.shape[-1], file=sys.stderr)
    sys.exit(13)
if existresult.dtype != np.int32 and existresult.dtype != np.int64:
    print("Expecting", countfile, "to have integer type", file=sys.stderr)
    sys.exit(14)
existresult = None

db, dbcurs = remdefaults.opendb()

try:
    bf = remfits.parse_filearg(biasfile, dbcurs, 'B')
except remfits.RemFitsErr as e:
    print("Open of bias file", biasfile, "gave error", e.args[0])
    sys.exit(20)

bfdims = bf.dims()
bfstartx, bfstarty, bfendx, bfendy = bfdims
bffilter = bf.filter
bfdata = bf.data

errors = 0
changes = 0

for file in files:

    prevsum = countresult.sum()

    try:
        ff = remfits.parse_filearg(file, dbcurs, type=typef)
    except remfits.RemFitsErr as e:
        print("Open of", file, "gave error", e.args[0], file=sys.stderr)
        errors += 1
        continue

    if ff.filter != bffilter:
        print(file, "filter of", ff.filter, "does not match bias file of", bffilter, file=sys.stderr)
        errors += 1
        continue

    if ff.dims() != bfdims:
        print(file, "has dimensions", ff.dims(), "whilst bias has dims", bfdims, file=sys.stderr)
        if not igngeom:
            errors += 1
            continue
        ffstartx, ffstarty, ffendx, ffendy = ff.dims()
        pstartx = max(bfstartx, ffstartx)
        pstarty = max(bfstarty, ffstarty)
        pendx = min(bfendx, ffendx)
        pendy = min(bfendy, ffendy)
        patch = ff.data[pstarty - ffstarty + trimsize:pendy - ffstarty - trimsize, pstartx - ffstartx + trimsize:pendx - ffstartx - trimsize] - \
            bfdata[pstarty - bfstarty + trimsize:pendy - bfstarty - trimsize, pstartx - bfstartx + trimsize:pendx - bfstartx - trimsize]
        countresult[pstarty + trimsize:pendy - trimsize, pstartx + trimsize:pendx - trimsize][patch <= 0] += 1
    else:
        patch = (ff.data - bfdata)[trimsize:-trimsize, trimsize:-trimsize]
        countresult[bfstarty + trimsize:bfendy - trimsize, bfstartx + trimsize:bfendx - trimsize][patch <= 0] += 1

    if prevsum != countresult.sum():
        changes += 1

if errors > 0:
    print("Stopping due to errors in", description, file=sys.stderr)
    sys.exit(20)

if changes != 0:
    print(changes, "changes in", description, file=sys.stderr)
    outf = open(countfile, 'rb+')
    fcntl.lockf(outf, fcntl.LOCK_EX)
    existresult = np.load(outf)
    outf.truncate(0)
    outf.seek(0)
    existresult += countresult
    np.save(outf, existresult)
    outf.close()
else:
    print("No changes in", description, file=sys.stderr)
