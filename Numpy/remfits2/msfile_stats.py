#!  /usr/bin/env python3

"""Print statisics from mean/std dev files"""

import remdefaults
import argparse
import sys
import numpy as np
import warnings


def disprow(name, arr):
    """Print a row of the array"""
    print("{name}:\t{min:8.1f} {med:8.1f} {max:8.1f} {mean:8.2f} {std:8.2f}".format(name=name, max=arr.max(), min=arr.min(), med=np.median(arr), mean=arr.mean(), std=arr.std()))

# Cope with divisions by zero


warnings.simplefilter('ignore', RuntimeWarning)

parsearg = argparse.ArgumentParser(description="Print statistics about mean/std dev files", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('msfiles', type=str, nargs='+', help='Input MS files')
remdefaults.parseargs(parsearg, tempdir=False, database=False)
parsearg.add_argument('--header', action='store_true', help="Print header")

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
msfiles = resargs['msfiles']

for file in msfiles:

    infile = remdefaults.meanstd_file(file)
    try:
        sourcearray = np.load(infile)
    except OSError as e:
        print("Cannot open source file", file, "error was", e.args[1], file=sys.stderr)
        continue

    counts = sourcearray[0].flatten()
    means = sourcearray[1].flatten()
    stds = sourcearray[2].flatten()
    mins = sourcearray[3].flatten()
    maxs = sourcearray[4].flatten()

    msk = counts != 0
    means = means[msk]
    stds = stds[msk]
    mins = mins[msk]
    maxs = maxs[msk]

    if file != infile:
        print(file, " (", infile, "):", sep='')
    else:
        print(file, ":", sep='')

    if resargs['header']:
        print("Stat\t     Min      Med      Max     Mean      Std")
    disprow("Means", means)
    disprow("Stds", stds)
    disprow("Minima", mins)
    disprow("Maxima", maxs)
    disprow("Ranges", maxs - mins)
