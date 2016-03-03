#! /usr/bin/env python

import sys
import os
import os.path
import string
import warnings
import argparse
import numpy as np
import numpy.random as nr

warnings.simplefilter('error')

parsearg = argparse.ArgumentParser(description='Cull randomly-selected rows in file', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', type=str, help='Infile Outfile', nargs=2)
parsearg.add_argument('--bycol', action='store_true', help='Cull columns rather than rows')
parsearg.add_argument('--cullperc', type=float, default=50.0, help='Percent cull')

resargs = vars(parsearg.parse_args())

infile, outfile = resargs['files']
bycol = resargs['bycol']
cullperc = resargs['cullperc'] / 100.0

if cullperc < 0.0 or cullperc >= 1.0:
    print "Invalid cull percent, should be between 0 and 100"
    sys.exit(10)

try:
    inf = np.loadtxt(infile)
except IOError:
    print "Cannot load file", infile
    sys.exit(11)

try:
    nrows, ncols = inf.shape
except ValueError:
    print "Invalid array shape in", infile
    sys.exit(12)

if bycol:
    rands = nr.uniform(size=ncols) >= cullperc
else:
    rands = nr.uniform(size=nrows) >= cullperc

if np.count_nonzero(rands) == 0:
    print "No randoms left after the cull, try culling less"
    sys.exit(1)

if bycol:
    outf = inf[:,rands]
else:
    outf = inf[rands]

try:
    np.savetxt(outfile, outf)
except IOError:
    print "Cannot save file", outfile
    sys.exit(11)
