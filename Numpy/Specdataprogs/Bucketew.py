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

results = []

for b in bits:
    if b.shape[1] == 1:
        results.append(b)
    r = np.zeros(shape=(8,1))
    r[0] = b[0].mean()
    r[1] = b[1].mean()
    r[2] = b[2].mean()
    r[3] = math.sqrt(np.square(b[3]).sum())    
    r[4] = b[4].mean()
    r[5] = math.sqrt(np.square(b[5]).sum())
    r[6] = b[6].prod() ** 1.0/b.shape[1]
    try:
        r[7] = math.exp(math.sqrt(np.sum(np.square(np.log(r[6]/r[7]))/b.shape[1])))
    except RuntimeWarning:
        pass
    results.append(r)

results = np.array(results)
timearray = results[0]
diffs = np.diff(timearray)
places = np.where(diffs > lonely)
 

np.savetxt(outfile, results)
