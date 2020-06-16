#!  /usr/bin/env python3

import remdefaults
import argparse
import sys
import os.path
import miscutils
import numpy as np


def get_argfile(arg):
    """Get argument file and possible :n plane.
    Abort with error if we don't understand it
    otherwise return 2D array"""
    global inlib
    bits = arg.split(':')
    if len(bits) > 1:
        if len(bits) > 2:
            print("Do not understand", arg, "expecting filename or filename:plane", file=sys.stderr)
            sys.exit(20)
        file, plane = bits
        try:
            plane = int(plane)
        except ValueError:
            print("Plane number in", arg, "should be integer", file=sys.stderr)
            sys.exis(21)
    else:
        plane = None
        file = bits[0]
    file = miscutils.addsuffix(file, ".npy")
    if inlib:
        file = remdefaults.get_libfile(file)
    try:
        arr = np.load(file)
    except OSError as e:
        print("Cannot load", file, "error was", e.args[1], file=sys.stderr)
        sys.exit(22)
    if plane is None:
        if len(arr.shape) == 2:
            return  arr
        print("file", file, "has dimension", len(arr.shape), "but no plane given", file=sys.stderr)
        sys.exit(23)
    elif len(arr.shape) == 3:
        try:
            return arr[plane]
        except IndexError:
            print("Plane", plane, "out of range for file", file, "which has dims", arr.shape, file=sys.stderr)
            sys.exit(24)
    else:
        print("Plane", plane, "given but", file, "has dimension", len(arr.sahpe), file=sys.stderr)
        sys.exit(25)


parsearg = argparse.ArgumentParser(description='Match up relative startx/starty between two tallied/ms arrays', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', nargs=2, type=str, help='File A and file B with :plene number if 3-D')
remdefaults.parseargs(parsearg)
parsearg.add_argument('--percentile', type=float, default=90, help='Percent above which we take as exceptional')
parsearg.add_argument('--inlib', action='store_true', help='Load and store in library return than CWD by default')
parsearg.add_argument('--offlim', type=int, default=100, help='Limits of offsets"')
resargs = vars(parsearg.parse_args())
files = resargs['files']
percentile = resargs['percentile']
inlib = resargs['inlib']
remdefaults.getargs(resargs)
offlim = resargs['offlim']

arra = get_argfile(files[0])
arrb = get_argfile(files[1])

perca = np.percentile(arra, percentile)
percb = np.percentile(arrb, percentile)
print("array a percentile", perca, "array b", percb)

bina = arra >= perca
binb = arrb >= percb

rowsa, colsa = bina.shape
rowsb, colsb = binb.shape

results = []

for rowoff in range(-offlim, offlim + 1):
    arstart = max(0, -rowoff)
    brstart = max(0, rowoff)
    commr = min(rowsa - arstart, rowsb - brstart)
    arend = arstart + commr
    brend = brstart + commr
    asub = bina[arstart:arend]
    bsub = binb[brstart:brend]
    for coloff in range(-offlim, offlim + 1):
        acstart = max(0, -coloff)
        bcstart = max(0, coloff)
        commc = min(colsa - acstart, colsb - bcstart)
        acend = acstart + commc
        bcend = bcstart + commc
        totm = np.count_nonzero(asub[:, acstart:acend] & bsub[:, bcstart:bcend])
        if totm != 0:
            results.append((totm, commr * commc, rowoff, coloff))

results.sort(key=lambda x: x[0] / x[1])
for totm, els, row, col in results:
    print("%3d %6d %4d %4d" % (totm, els, row, col))
