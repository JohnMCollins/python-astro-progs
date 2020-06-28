#!  /usr/bin/env python3

import remdefaults
import argparse
import sys
import os.path
import miscutils
import arrayfiles
import numpy as np

parsearg = argparse.ArgumentParser(description='Match up relative startx/starty between two tallied/ms arrays', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', nargs=2, type=str, help='File A and file B with :plene number if 3-D')
remdefaults.parseargs(parsearg, inlib=False, tempdir=False)
parsearg.add_argument('--percentile', type=float, default=90, help='Percent above which we take as exceptional')
parsearg.add_argument('--offlim', type=int, default=100, help='Limits of offsets"')
resargs = vars(parsearg.parse_args())
files = resargs['files']
percentile = resargs['percentile']
remdefaults.getargs(resargs)
offlim = resargs['offlim']

try:
    arra = arrayfiles.get_argfile(files[0])
    arrb = arrayfiles.get_argfile(files[1])
except arrayfiles.ArrayFileError as e:
    print(e.args[0], file=sys.stderr)
    sys.exit(20)

perca = np.percentile(arra, percentile)
percb = np.percentile(arrb, percentile)
print("array a percentile", perca, "array b", percb)

bina = arra >= perca
binb = arrb >= percb

rowsa, colsa = bina.shape
rowsb, colsb = binb.shape

results = []

# Kick off looking for columns without worrying about rows

rend = min(rowsa, rowsb)
asub = bina[0:rend]
bsub = binb[0:rend]

for coloff in range(-offlim, offlim + 1):
    acstart = max(0, -coloff)
    bcstart = max(0, coloff)
    commc = min(colsa - acstart, colsb - bcstart)
    acend = acstart + commc
    bcend = bcstart + commc
    totm = np.count_nonzero(asub[:, acstart:acend] & bsub[:, bcstart:bcend])
    if totm != 0:
        results.append((totm, rend * commc, 0, coloff))

results.sort(key=lambda x: x[0] / x[1])
colshift = results[-1][3]

print("Calculated column shift as", colshift)
acstart = max(0, -colshift)
bcstart = max(0, colshift)
commc = min(colsa - acstart, colsb - bcstart)
acend = acstart + commc
bcend = bcstart + commc
asub = bina[:, acstart:acend]
bsub = binb[:, bcstart:bcend]

results = []

for rowoff in range(-offlim, offlim + 1):
    arstart = max(0, -rowoff)
    brstart = max(0, rowoff)
    commr = min(rowsa - arstart, rowsb - brstart)
    arend = arstart + commr
    brend = brstart + commr
    totm = np.count_nonzero(asub[arstart:arend] & bsub[brstart:brend])
    if totm != 0:
        results.append((totm, commr * commc, rowoff, colshift))

results.sort(key=lambda x: x[0] / x[1])
lresults = min(len(results), 10)
if lresults == 0:
    print("No results")
    sys.exit(0)

for totm, els, row, col in results[-lresults:]:
    print("%3d %6d %4d" % (totm, els, row))
