#!  /usr/bin/env python3

import dbops
import remdefaults
import argparse
import sys
import os.path
import miscutils
import numpy as np
import remfits
import remdefaults
import warnings
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

parsearg = argparse.ArgumentParser(description='Display rows and columns where counts go -ve or zero', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg, tempdir=False, libdir=False)
parsearg.add_argument('files', type=str, nargs='+', help='Files to find zero rows/columns in')
parsearg.add_argument('--biasfile', type=str, required=True, help='Bias file to use')
parsearg.add_argument('--trim', type=int, default=0, help='Amount to effectively trim off each edge')
parsearg.add_argument('--nzeros', type=int, default=1, help='Limit output to rows/columns with this number of zeros/neg')
parsearg.add_argument('--bycols', action='store_true', help='Consider columns, default by rows')
parsearg.add_argument('--flats', action='store_true', help='Take files as flat files')
parsearg.add_argument('--criterion', type=float, default=0.0, help='Value to consider exceptional')

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
files = resargs['files']
biasfile = resargs['biasfile']
trim = resargs['trim']
nzeros = resargs['nzeros']
bycols = resargs['bycols']
ftype = None
if resargs['flats']:
    ftype = 'F'
crit = resargs['criterion']

mydb, mycurs = remdefaults.opendb()

try:
    bf = remfits.parse_filearg(biasfile, mycurs, 'B')
except remfits.RemFitsErr as e:
    print("Biasfile", biasfile, "error", e.args[0], file=sys.stderr)
    sys.exit(10)

bdims = bf.dimscr()
bdata = bf.data

minrow = mincol = trim
maxrow = bf.nrows - trim
maxcol = bf.ncolumns - trim

for file in files:

    try:
        ff = remfits.parse_filearg(file, mycurs, ftype)
    except remfits.RemFitsErr as e:
        print("Could not open", file, "error", e.args[0], file=sys.stderr)
        continue

    if ff.dimscr() != bdims:
        print("Dimensions of", file, "does not match bias", file=sys.stderr)
        continue

    fdat = ff.data
    diffs = fdat - bdata
    if np.count_nonzero(diffs <= crit) == 0:
        print(file + ": ", "No negative or zeros in differences for", file)
        continue

    bycol = dict()
    byrow = dict()

    mrows, mcols = np.where(diffs <= crit)
    for r, c in zip(mrows, mcols):
        if r >= minrow and r < maxrow and c >= mincol and c < maxcol:
            try:
                bycol[c].append(r)
            except KeyError:
                bycol[c] = [r]
            try:
                byrow[r].append(c)
            except KeyError:
                byrow[r] = [c]

    if nzeros > 1:
        dlist = []
        for k, v in bycol.items():
            if len(v) < nzeros:
                dlist.append(k)
        for d in dlist:
            del bycol[d]
        dlist = []
        for k, v in byrow.items():
            if len(v) < nzeros:
                dlist.append(k)
        for d in dlist:
            del byrow[d]

    if bycols:
        if len(bycol) == 0:
            print(file + ": ", "No negative or zeros columns left after pruning to trim", trim, "and nzeros", nzeros, "in", file)
            continue
        print("File:", file)
        for c in sorted(bycol.keys()):
            l = bycol[c]
            print("{}:".format(c), " ".join([str(i) for i in sorted(l)]))
    else:
        if len(byrow) == 0:
            print(file + ": ", "No negative or zeros rows left after pruning to trim", trim, "and nzeros", nzeros, "in", file)
            continue
        print("File:", file)
        for r in sorted(byrow.keys()):
            l = byrow[r]
            print("{}:".format(r), " ".join([str(i) for i in sorted(l)]))
