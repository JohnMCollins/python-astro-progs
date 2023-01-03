#!  /usr/bin/env python3

"""Assign an initial value of brightness based on mean/std of initial calcs"""

import argparse
import sys
import math
import numpy as np
import remdefaults
import objdata

parsearg = argparse.ArgumentParser(description='Set initial brightness values from aducalc records in DB', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg, tempdir=False, inlib=False)
parsearg.add_argument('target', type=str, nargs=1, help='Target object to search in vicinity')
parsearg.add_argument('--filter', type=str, required=True, help='Filter in question')
parsearg.add_argument('--minoccs', type=int, default=5, help='Minimum number of occurences to consider object')
parsearg.add_argument('--nstds', type=float, help='Clip ADU calculations this number of STDs away')
parsearg.add_argument('--update', action='store_true', help='Update existing values else leave alone')

resargs = vars(parsearg.parse_args())
target = resargs['target']
remdefaults.getargs(resargs)
filt = resargs['filter']
minoccs = resargs['minoccs']
nstds = resargs['nstds']
update = resargs['update']

mydb, mycu = remdefaults.opendb()

try:
    tobj = objdata.ObjData(name=target)
    tobj.get(mycu)
except objdata.ObjDataError as e:
    print("Cannot find target object", target, "error was", e.args[0], file=sys.stderr)
    sys.exit(10)

if not tobj.is_target():
    print(target, "is not a target but in vicinity of", tobj.vicinity, file=sys.stderr)
    sys.exit(11)

tobjind = tobj.objind
vicinity = tobj.vicinity

fieldselect = []
fieldselect.append('filter=' + mydb.escape(filt))
fieldselect.append('vicinity=' + mydb.escape(vicinity))

if not update:
    fieldselect.append(filt + 'bri IS NULL')

selectstatement = "SELECT objind,aducount,aduerr " \
                    "FROM aducalc INNER JOIN obsinf ON aducalc.obsind=obsinf.obsind " \
                    "INNER JOIN objdata ON aducalc.objind=objdata.ind " \
                    "WHERE " + " AND ".join(fieldselect)

mycu.execute(selectstatement)
rows = mycu.fetchall()

resdict = dict()

for objind, count, err in rows:
    try:
        resdict[objind].append((count, err))
    except KeyError:
        resdict[objind] = [(count, err)]

for objind, counterr in  resdict.items():
    if len(counterr) < minoccs:
        print("Skipping", objind, "only", len(counterr), "items", file=sys.stderr)
        continue
    counterr = np.array(counterr)
    counts = counterr[:,0]
    errs = counterr[:,1]
    meanvs = counts.mean()
    if nstds is not None:
        stdvs = counts.std()
        mask = np.abs(counts - meanvs) <= nstds * stdvs
        if np.count_nonzero(mask) < minoccs:
            print("Skipping", objind, "only", np.count_nonzero(mask), "left after clipping to", nstds, "std devs of ", stdvs, file=sys.stderr)
            continue
        counts = counts[mask]
        errs = errs[mask]
        meanvs = counts.mean()
    num = len(errs)
    stvs = math.sqrt(np.sum(errs**2))/num
    print("{:8d} {:4d} {:10.2f} {:10.2f}".format(objind, num, meanvs, stvs))
    mycu.execute("UPDATE objdata SET {filt:s}bri={mv:.9e},{filt:s}brisd={sd:.9e} WHERE ind={oi:d}".format(filt=filt,mv=meanvs,sd=stvs,oi=objind))
mydb.commit()
