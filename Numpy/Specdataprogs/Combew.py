#! /usr/bin/env python

import sys
import os
import os.path
import string
import warnings
import argparse
import numpy as np

warnings.simplefilter('error')

parsearg = argparse.ArgumentParser(description='Combine EW files with scales for EW and PR', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('ewfiles', type=str, help='Specinfo file', nargs=3)
parsearg.add_argument('--ewmult', type=float, default=1.0, help='Factor to multiply second EW file')
parsearg.add_argument('--prpower', type=float, default=1.0, help='Power to apply to second PR file')
parsearg.add_argument('--force', action='store_true', help='OK to overwrite existing output file')

res = vars(parsearg.parse_args())

infile1, infile2, outfile = res['ewfiles']
ewmult = res['ewmult']
prpower = res['prpower']

if not res['force'] and os.path.isfile(outfile):
    print "Will not overwrite existing", outfile
    sys.exit(10)

try:
    inf1 = np.loadtxt(infile1, unpack=True)
except IOError:
    print "Cannot load file", infile1
    sys.exit(11)
try:
    inf2 = np.loadtxt(infile2, unpack=True)
except IOError:
    print "Cannot load file", infile2
    sys.exit(11)

inf1[2] += inf2[2] * ewmult
inf1[2] /= abs(ewmult) + 1

inf1[6] *= inf2[6] ** prpower
if prpower != -1.0:
    inf1[6] **= 1.0/(prpower+1.0)

np.savetxt(outfile, inf1.transpose())
sys.exit(0)
