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
remdefaults.parseargs(parsearg, inlib=False, tempdir=False, database=False)
parsearg.add_argument('--anstd', type=float, default=5, help='Number of std devs in file A above which we take as exceptional')
parsearg.add_argument('--bnstd', type=float, default=5, help='Number of std devs in file A above which we take as exceptional')
parsearg.add_argument('--offlim', type=int, default=100, help='Limits of offsets"')
resargs = vars(parsearg.parse_args())
files = resargs['files']
anstd = resargs['anstd']
bnstd = resargs['bnstd']
remdefaults.getargs(resargs)
offlim = resargs['offlim']

try:
    arra = arrayfiles.get_argfile(files[0])
    arrb = arrayfiles.get_argfile(files[1])
except arrayfiles.ArrayFileError as e:
    print(e.args[0], file=sys.stderr)
    sys.exit(20)

bina = arra >= arra.mean() + anstd * arra.std()
binb = arrb >= arrb.mean() + bnstd * arrb.std()

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
