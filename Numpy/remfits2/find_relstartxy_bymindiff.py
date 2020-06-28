#!  /usr/bin/env python3

import remdefaults
import argparse
import sys
import os.path
import miscutils
import arrayfiles
import numpy as np

parsearg = argparse.ArgumentParser(description='Match up relative startx/starty between two tallied/ms arrays v2', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', nargs=2, type=str, help='File A and file B with :plene number if 3-D')
remdefaults.parseargs(parsearg, inlib=False, tempdir=False)
parsearg.add_argument('--offlim', type=int, default=100, help='Limits of offsets"')
resargs = vars(parsearg.parse_args())
files = resargs['files']
remdefaults.getargs(resargs)
offlim = resargs['offlim']

try:
    arra = arrayfiles.get_argfile(files[0])
    arrb = arrayfiles.get_argfile(files[1])
except arrayfiles.ArrayFileError as e:
    print(e.args[0], file=sys.stderr)
    sys.exit(20)

rowsa, colsa = arra.shape
rowsb, colsb = arrb.shape

results = []

for rowoff in range(-offlim, offlim + 1):
    arstart = max(0, -rowoff)
    brstart = max(0, rowoff)
    commr = min(rowsa - arstart, rowsb - brstart)
    arend = arstart + commr
    brend = brstart + commr
    asub = arra[arstart:arend]
    bsub = arrb[brstart:brend]
    for coloff in range(-offlim, offlim + 1):
        acstart = max(0, -coloff)
        bcstart = max(0, coloff)
        commc = min(colsa - acstart, colsb - bcstart)
        acend = acstart + commc
        bcend = bcstart + commc
        totm = np.sum(np.abs(asub[:, acstart:acend] - bsub[:, bcstart:bcend]))
        numb = commr * commc
        results.append((totm / numb, totm, numb, rowoff, coloff))

print("By prop")
results.sort(key=lambda x: x[0], reverse=True)
for prop, totm, els, row, col in results[-10:]:
    print("%8.4f %3d %6d %4d %4d" % (prop, totm, els, row, col))

print("By total")
results.sort(key=lambda x: x[1], reverse=True)
for prop, totm, els, row, col in results[-10:]:
    print("%8.4f %3d %6d %4d %4d" % (prop, totm, els, row, col))
