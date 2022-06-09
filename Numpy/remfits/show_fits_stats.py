#!  /usr/bin/env python3

"""Reject a FITS file with a reason"""

import argparse
import sys
import warnings
import numpy as np
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
import miscutils
import remdefaults
import remfits

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

parsearg = argparse.ArgumentParser(description='Display paramaters of section of FITS file',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', type=str, nargs='*', help='Files or ids to process')
parsearg.add_argument('--trimleft', type=int, default=0, help='Pixels to trim off left')
parsearg.add_argument('--trimright', type=int, default=0, help='Pixels to trim off right')
parsearg.add_argument('--trimtop', type=int, default=0, help='Pixels to trim off top')
parsearg.add_argument('--trimbottom', type=int, default=0, help='Pixels to trim off bottom')
parsearg.add_argument('--header', action='store_true', help='Print a header line')
remdefaults.parseargs(parsearg)

resargs = vars(parsearg.parse_args())
files = resargs['files']
remdefaults.getargs(resargs)
trimleft = resargs['trimleft']
trimright = resargs['trimright']
trimtop = resargs['trimtop']
trimbottom = resargs['trimbottom']
pheader = resargs['header']

mydb, mycu = remdefaults.opendb()

errors = 0

fsize = max([len(miscutils.removesuffix(f, allsuff=True)) for f in files])

if pheader:
    print("{:{fsize}s} {:>7s} {:>8s} {:>8s} {:>8s} {:>8s}".format("File", "Min", "Max", "Median", "Mean", "Std", fsize=fsize))

for file in files:

    try:
        ff = remfits.parse_filearg(file, mycu)
    except remfits.RemFitsErr as e:
        print("Open of", file, "gave error", e.args[0], file=sys.stderr)
        errors += 1
        continue

    data = ff.data
    if trimleft > 0:
        data = data[:, trimleft:]
    if trimright > 0:
        data = data[:, :-trimright]
    if trimtop > 0:
        data = data[:-trimtop]
    if trimbottom > 0:
        data = data[trimbottom:]

    print("{:{fsize}s} {:7.2f} {:8.2f} {:8.2f} {:8.2f} {:8.2f}".format(miscutils.removesuffix(file, allsuff=True), data.min(), data.max(), np.median(data), data.mean(), data.std(), fsize=fsize))

if errors != 0:
    sys.exit(1)
