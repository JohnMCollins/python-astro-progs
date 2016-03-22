#! /usr/bin/env python

import sys
import os
import os.path
import argparse
import numpy as np
import math
import string
import warnings
import jdate

warnings.simplefilter('error')

parsearg = argparse.ArgumentParser(description='Group up obs file by combining obs close together', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('ifiles', type=str, help='Infile Outfile', nargs=2)
parsearg.add_argument('--sepdays', type=float, default=1.0, help='Criterion for split')
parsearg.add_argument('--lonely', type=float, default=1e6, help='Remove single items this far from others')
parsearg.add_argument('--tcol', type=int, default=0, help='Column used for time periods')
parsearg.add_argument('--force', action='store_true', help='OK to overwrite existing output file')

resargs = vars(parsearg.parse_args())

infile, outfile = resargs['ifiles']

if not resargs['force'] and os.path.isfile(outfile):
    print "Will not overwrite existing", outfile
    sys.exit(10)

try:
    inf = np.loadtxt(infile, unpack=True)
except ValueError:
    print infile, "is not a table of numbers"
    sys.exit(12)

ncols = inf.shape[0]

sepdays = resargs['sepdays']
lonely = resargs['lonely']
tcol = resargs['tcol']
timearray = inf[tcol]
diffs = np.diff(timearray)
places = np.where(diffs >= sepdays)[0] + 1
bits = []
lastp = 0

for p in places:
    bits.append(inf[:,lastp:p])
    lastp = p

if lastp < len(timearray):
    bits.append(inf[:,lastp:])

results = np.zeros(shape=(0,ncols))

for b in bits:
    results = np.concatenate((results, b.mean(axis=1).reshape(1,ncols)))

timearray = results[:,tcol]
diffs = np.diff(timearray)
places = np.where(diffs >= lonely)[0]
if len(places) != 0:
    wb = np.concatenate(((-1,), places)) + 1
    we = np.concatenate((places,(len(diffs),)))
    llist = list(set(wb)&set(we))
    if len(llist) != 0:
        llist.sort()
        for ll in llist:
            print "Deleted isolated point at", jdate.display(timearray[ll])
        results = np.delete(results, llist, axis=0)
    else:
        print "No isolated points found"
np.savetxt(outfile, results)

print "%d original points, %d after binning, %d after removal of lonely points" % (inf.shape[1], len(timearray), results.shape[0])
