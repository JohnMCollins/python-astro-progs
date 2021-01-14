#!  /usr/bin/env python3

# Duplicate creation of master flat file

from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
from astropy.io import fits
from astropy.time import Time
import datetime
import numpy as np
import argparse
import warnings
import sys
import remdefaults
import remfits
import col_from_file

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)
warnings.simplefilter('error', RuntimeWarning)  # Want div by zero etc to retunr error

parsearg = argparse.ArgumentParser(description='Display statistics of bad pixel neighbours ', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', nargs='*', type=str, help='Filenames or obsinds to process, otherwise use stdin')
parsearg.add_argument('--colnum', type=int, default=0, help='Column to use from stdin')
remdefaults.parseargs(parsearg, tempdir=False, libdir=False)
parsearg.add_argument('--trim', type=int, default=0, help="Pixels to trim from each edge")
parsearg.add_argument('--biasfile', type=str, required=True, help="Bias file to use")
parsearg.add_argument('--bthresh', type=float, default=3, help='Threhold (number of stds) to regard as part of signal')

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
files = resargs['files']
trim = resargs['trim']
biasfile = resargs['biasfile']
bthreash = resargs['bthresh']

if len(files) == 0:
    files = col_from_file.col_from_file(sys.stdin, resargs['colnum'])

mydb, dbcurs = remdefaults.opendb()

try:
    bfile = remfits.parse_filearg(biasfile, dbcurs, 'B')
except remfits.RemFitsErr as e:
    print("Cannot open bias file", biasfile, "error was", e.args[0], file=sys.stderr)
    sys.exit(20)

bdata = bfile.data
if trim != 0:
    bdata = bdata[trim:-trim, trim:-trim]

bneab = bdata.mean()
bstd = bdata.std()

tot_neg = tot_negnext = tot_neigh = 0

try:
    for f in files:
        try:
            rf = remfits.parse_filearg(f, dbcurs)
        except remfits.RemFitsErr as e:
            print("File", f, "gave error", e.args[0], file=sys.stderr)
            continue
        fdata = rf.data
        if trim != 0:
            fdata = fdata[trim:-trim, trim:-trim]
        fmean = fdata.mean()
        thresh = fdata.std() * bthreash
        diffs = fdata - bdata
        fbase = fdata - fmean
        rw, cw = np.where(diffs < 0)
        nneg = rw.shape[0]
        negn = 0
        posn = 0
        for r, c in zip(rw, cw):
            neighbours_diff = []
            neighbours_plus = []
            for dr, dc in [(r, c) for r in (-1, 0, 1) for c in (-1, 0, 1) if r != c]:
                try:
                    neighbours_diff.append(diffs[r + dr, c + dc])
                    neighbours_plus.append(fbase[r + dc, c + dc])
                except IndexError:
                    pass
            negn += np.count_nonzero(np.array(neighbours_diff) < 0)
            posn += np.count_nonzero(np.array(neighbours_plus) > thresh)
        print("{:<20s}{:%Y-%m-%d %H:%M:%S}: {:8d}{:8d}{:8d}".format(f, rf.date, nneg, negn, posn))
        tot_neg += nneg
        tot_negnext += negn
        tot_neigh += posn
except (KeyboardInterrupt, BrokenPipeError):
    pass

print("\n{:<20s}Total: {:22d}{:8d}{:8d}".format("", tot_neg, tot_negnext, tot_neigh))
