#!  /usr/bin/env python3

"""Make individual histograms for each pixel"""

import argparse
import sys
import os.path
import warnings
import remdefaults
import miscutils
import numpy as np
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
parsearg.add_argument('--force', action='store_true', help='Force create new file on top of existing')
parsearg.add_argument('--prefix', required=True, type=str, help='Result file prefix')
parsearg.add_argument('--trim', type=int, default=0, help='Amount to trim each edge of image')
parsearg.add_argument('--bins', type=float, nargs='+', required=True, help='Bins of histogram')
parsearg.add_argument('--verbose', action='store_true', help='Give stats')

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
files = resargs['files']
create = resargs['create']
prefix = resargs['prefix']
ftype = resargs['type']
force = resargs['force']
trim = resargs['trim']
bins = sorted(resargs['bins'])
verbose = resargs['verbose']

if bins[0] > 0.0:
    bins.insert(0, 0.0)

numbins = len(bins)

gtype = None
if ftype == 'flat':
    gtype = 'F'
elif ftype == 'bias':
    gtype = 'B'

if len(files) == 0:
    files = col_from_file.col_from_file(sys.stdin, resargs['colnum'])

outfile = miscutils.addsuffix(prefix, 'hist')

if create:
    if not force:
        if os.path.exists(outfile):
            print("Output file", outfile, "already exists - aborting use --force if needed", file=sys.stderr)
            sys.exit(11)
    count_array = np.zeros((numbins, 2048, 2048), dtype=np.uint32)
else:
    try:
        count_array = np.load(outfile)
    except OSError as e:
        print("Cannot open", e.filename, "error was", e.args[1], file=sys.stderr)
        sys.exit(12)
    if count_array.shape != (numbins, 2048, 2028):
        print("Shape mismatch expected", (numbins, 2048, 2048), "read", count_array.shape, file=sys.stderr)
        sys.exit(13)

dbase, dbcurs = remdefaults.opendb()

for file in files:
    try:
        ff = remfits.parse_filearg(file, dbcurs, gtype)
    except remfits.RemFitsErr as e:
        print("Could not fetch file", file, "error was", e.args[0], file=sys.stderr)
        continue

    if verbose:
        print("Looking at", file, "filter", ff.filter, file=sys.stderr)

    fdat = ff.data
    if trim != 0:
        fdat = fdat[trim:-trim, trim:-trim]
    startx = ff.startx + trim
    starty = ff.starty + trim
    endr = ff.endy - trim
    endc = ff.endx - trim

    try:
        for n, bv in enumerate(bins):
            compar = fdat >= bv
            nz = np.count_nonzero(compar)
            if nz == 0:
                if verbose:
                    print("Nothing above {:.6g}".format(bv), file=sys.stderr)
                break
            if verbose:
                print("{:d} values above {:.6g}".format(nz, bv), file=sys.stderr)
            count_array[n, starty:endr, startx:endc] += compar
    except ValueError:
        print("Wrong size file = ", file, "r/c/sx/sy", endr - starty, endc - startx, startx, starty, file=sys.stderr)

for n in range(0, numbins - 1):
    count_array[n] -= count_array[n + 1]

with open(outfile, "wb") as outf:
    np.save(outf, count_array)
