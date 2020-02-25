#!  /usr/bin/env python3

from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
from astropy.io import fits
import argparse
import datetime
import re
import sys
import warnings
import remgeom
import trimarrays
import numpy as np
import miscutils
import copy


class hotspot(object):
    """Record details of hotspot"""

    def __init__(self, file, row, col, val):
        self.file = file
        self.row = int(row)
        self.col = int(col)
        self.value = val

    def __hash__(self):
        return self.row * 1024 + self.col

    def __eq__(self, other):
        return self.row == other.row and self.col == other.col

def ptrail(s, e):
    """Print trailing stuff"""
    if e != s:
        print("\t%d - %d" % (s, e))
    else:
        print("\t%d" % s)

# Shut up warning messages


warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

parsearg = argparse.ArgumentParser(description='Get list of hotspots in one or more filess',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', type=str, nargs='+', help='List of files to select grom')
parsearg.add_argument('--nstd', type=float, default=5.0, help='Number of std devs to select from')
parsearg.add_argument('--trim', type=int, default=100, help='Ammount to trim each side')
parsearg.add_argument('--percent', type=float, default=1.0, help='Percentage of files hotspot is in to consider significant')

resargs = vars(parsearg.parse_args())

files = resargs['files']
nstd = resargs['nstd']
trimsides = resargs['trim']
percent = resargs['percent']

resarray = []

filesdone = dict()

for file in files:

    if file in filesdone:
        continue

    try:
        ff = fits.open(file)
    except OSError as e:
        print("Cannot open", file, e.strerror, file=sys.stderr)
        continue

    fdat = ff[0].data
    ff.close()
    stripf = miscutils.removesuffix(file, all=True)

    fdat = trimarrays.trimzeros(trimarrays.trimnan(fdat))
    trimmed = fdat.copy()
    if trimsides > 0:
        trimmed = trimmed[trimsides:-trimsides, trimsides:-trimsides]
    fm = trimmed.mean()
    hotval = fm + trimmed.std() * nstd

    rwh, cwh = np.where(fdat > hotval)

    for r, c in zip(rwh, cwh):
        resarray.append(hotspot(stripf, r, c, fdat[r, c]))

    filesdone[file] = 1

collated = dict()

if len(resarray) == 0:
    print("No hotspots found anywhere", file=sys.stderr)
    sys.exit(1)

for res in resarray:

    try:
        orig = collated[res]
    except KeyError:
        orig = []

    orig.append(res)
    collated[res] = orig

nthresh = len(filesdone) * percent / 100.0
pc = 100.0 / len(filesdone)

selected = []
for v in collated.values():
    if len(v) >= nthresh:
        selected.append((v[0].row, v[0].col, len(v)))

byvalrowcol = sorted(sorted(sorted(selected, key=lambda x: x[1]), key=lambda x: x[0]), key=lambda x: x[2], reverse=True)
byvalcolrow = sorted(sorted(sorted(selected, key=lambda x: x[0]), key=lambda x: x[1]), key=lambda x: x[2], reverse=True)
rowcol = sorted(sorted(selected, key=lambda x: x[1]), key=lambda x: x[0])
colrow = sorted(sorted(selected, key=lambda x: x[0]), key=lambda x: x[1])

lastval = -9

print("By value, row, column:")
for r, c, v in byvalrowcol:
    if v != lastval:
        print("%d occurences %7.2f:" % (v, v * pc))
        lastval = v
    print("\t%4d%4d" % (r, c))

lastval = -9

print("By value, column, row")
for r, c, v in byvalcolrow:
    if v != lastval:
        print("%d occurences %7.2f:" % (v, v * pc))
        lastval = v
    print("\t%4d%4d" % (r, c))

print("By row")
lastval = -9
stsq = endsq = -100

for r, c, v in rowcol:
    if lastval != r:
        print("Row %d" % r)
        lastval = r
        if stsq >= 0:
            ptrail(stsq, endsq)
            stsq = endsq = -100
    if endsq == c - 1:
        endsq = c
    else:
        if stsq >= 0:
            ptrail(stsq, endsq)
        stsq = endsq = c

if stsq >= 0:
    ptrail(stsq, endsq)
    stsq = endsq = -100

lastval = -9
for r, c, v in colrow:
    if lastval != c:
        print("Column %d" % c)
        lastval = c
        if stsq >= 0:
            ptrail(stsq, endsq)
            stsq = endsq = -100
    if endsq == r - 1:
        endsq = r
    else:
        if stsq >= 0:
            ptrail(stsq, endsq)
        stsq = endsq = r
if stsq >= 0:
    ptrail(stsq, endsq)
    stsq = endsq = -100

