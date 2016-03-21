#! /usr/bin/env python

import sys
import os
import os.path
import argparse
import numpy as np
import math
import warnings

warnings.simplefilter('error')

parsearg = argparse.ArgumentParser(description='Group up EW file by bucketing obs close together', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('ewfiles', type=str, help='Infile Outfile', nargs=2)
parsearg.add_argument('--sepdays', type=float, default=1.0, help='Criterion for split')
parsearg.add_argument('--lonely', type=float, default=1e6, help='Remove single items this far from others')
parsearg.add_argument('--force', action='store_true', help='OK to overwrite existing output file')

resargs = vars(parsearg.parse_args())

infile, outfile = resargs['ewfiles']

if not resargs['force'] and os.path.isfile(outfile):
    print "Will not overwrite existing", outfile
    sys.exit(10)

try:
    inf = np.loadtxt(infile, unpack=True)
    if inf.shape[0] != 8:
        raise ValueError("Bad shape")
except ValueError:
    print infile, "does not look like an EW file"
    sys.exit(12)

sepdays = resargs['sepdays']
lonely = resargs['lonely']

timearray = inf[0]
diffs = np.diff(timearray)
places = np.where(diffs >= sepdays)[0] + 1
bits = []
lastp = 0

for p in places:
    bits.append(inf[:,lastp:p])
    lastp = p

if lastp < len(timearray):
    bits.append(inf[:,lastp:])

results = np.zeros(shape=(0,8))

for b in bits:
    if b.shape[1] == 1:
        results = np.concatenate((results, b.transpose()))
    else:
        jd = b[0].mean()
        bjd = b[1].mean()
        ew = b[2].mean()
        ewe = math.sqrt(np.square(b[3]).sum())    
        ps = b[4].mean()
        pse = math.sqrt(np.square(b[5]).sum())
        pr = b[6].prod() ** 1.0/b.shape[1]
        try:
            pre = math.exp(math.sqrt(np.sum(np.square(np.log(b[6]/b[7]))/b.shape[1])))
        except RuntimeWarning:
            pre = 0.0
        results = np.concatenate((results, np.array([jd,bjd,ew,ewe,ps,pse,pr,pre]).reshape(1,8)))
timearray = results[:,0]
diffs = np.diff(timearray)
places = np.where(diffs >= lonely)[0]
if len(places) != 0:
    wb = np.concatenate(((-1,), places)) + 1
    we = np.concatenate((places,(len(diffs),)))
    results = np.delete(results, list(set(wb)&set(we)), axis=0)
np.savetxt(outfile, results)
