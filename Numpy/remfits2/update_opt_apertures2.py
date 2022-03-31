#!  /usr/bin/env python3

"""Run through apopt files display and optionally update apertures in database"""

import argparse
import sys
import math
import miscutils
import numpy as np
import remdefaults
import apopt


def pparts(hdr, dct):
    """Display results for overall or filter"""
    if np.count_nonzero(dct) == 0:
        return
    print("\t" + hdr)
    print("\t", end='')
    for n in range(1, 30):
        v = dct[n]
        if v == 0:
            continue
        print("\t{:d}:{:d}".format(n, v), end='')
    print()
    print("\tPeak at {:d} mean at {:d}".format(dct.argmax(), round(np.sum(np.arange(0, 30) * dct) / np.sum(dct))))


class opt_aps:
    """Remember stuff about each aperture"""

    def __init__(self, name, ind):
        self.objname = name
        self.objind = ind
        self.totfilts = np.zeros(30, dtype=np.uint32)
        self.byfilt = dict(g=np.zeros(30, dtype=np.uint32), i=np.zeros(30, dtype=np.uint32), r=np.zeros(30, dtype=np.uint32), z=np.zeros(30, dtype=np.uint32))

    def update(self, apsize, filt):
        """Update totals for object"""
        self.totfilts[apsize] += 1
        self.byfilt[filt][apsize] += 1

    def printap(self):
        """Print details"""
        print(self.objname, ":", sep='')
        pparts("Overall", self.totfilts)
        for filt in 'girz':
            pparts("Filter " + filt, self.byfilt[filt])


aotab = dict()

parsearg = argparse.ArgumentParser(description='Display the best apertures from run of get_opt_apertures', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', nargs='+', type=str, help='Get_opt_appertures results')
remdefaults.parseargs(parsearg, tempdir=False)
parsearg.add_argument('--update', action='store_true', help='Update database with results')

resargs = vars(parsearg.parse_args())
flist = resargs['files']
remdefaults.getargs(resargs)
update = resargs['update']

if update:
    mydb, mycurs = remdefaults.opendb()

donef = 0

for ffile in flist:

    donef += 1
    pref = miscutils.removesuffix(ffile, allsuff=True)

    try:
        rstr = apopt.load_apopts_from_file(pref)
    except apopt.ApOptErr as e:
        print(e.args[0], file=sys.stderr)
        continue

    for r in rstr.resultlist:
        try:
            ao = aotab[r.objname]
        except KeyError:
            ao = opt_aps(r.objname, r.objind)
            aotab[r.objname] = ao
        ao.update(r.apsize, rstr.filter)

if update:
    nupd = 0
    rng = np.arange(0, 30, dtype=np.float32)
    for objname, ao in aotab.items():
        numoccs = np.sum(ao.totfilts)
        meanv = np.sum(ao.totfilts * rng) / numoccs
        apstd = math.sqrt(np.sum(ao.totfilts * (rng - meanv) ** 2) / numoccs)
        mycurs.execute("SELECT apsize,apstd,basedon FROM objdata WHERE ind={ind:d}".format(ind=ao.objind))
        rs = mycurs.fetchall()
        oldapsize, oldapstd, oldnumoccs = rs[0]
        meanv = round(meanv)
        if oldapstd is None:
            oldapstd = 0
        if oldapsize != meanv or numoccs != oldnumoccs or round(oldapstd, 2) != round(apstd, 2):
            mycurs.execute("UPDATE objdata SET apsize={apsz:d},apstd={apstd:.6f},basedon={based:d} WHERE ind={ind:d}". \
                           format(apsz=meanv, apstd=apstd, based=numoccs, ind=ao.objind))
            if oldapsize == meanv:
                if oldapstd < apstd:
                    print("Raising std for {:s} apsize {:d} old {:.4f} new {:.4f}".format(objname, oldapsize, oldapstd, apstd))
                else:
                    print("Reducing std for {:s} apsize {:d} old {:.4f} new {:.4f}".format(objname, oldapsize, oldapstd, apstd))
            elif oldapsize == 0:
                print("Setting initial apsize for {:s} to {:d}".format(objname, meanv))
            else:
                print("Updated {:s} from {:d} to {:d} std from {:.4f} to {:.4f}".format(objname, oldapsize, meanv, oldapstd, apstd))
            nupd += 1
    if nupd > 0:
        mydb.commit()
try:
    for objname in sorted(aotab.keys()):
        aotab[objname].printap()
except (KeyboardInterrupt, BrokenPipeError):
    sys.exit(0)
