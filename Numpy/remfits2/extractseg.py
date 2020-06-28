#!  /usr/bin/env python3

import dbops
import remdefaults
import argparse
import sys
import os.path
import dbremfitsobj
import miscutils
import numpy as np
import warnings

# Cope with divisions by zero

warnings.simplefilter('ignore', RuntimeWarning)

parsearg = argparse.ArgumentParser(description='Extract required segment of tally file', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('tfile', type=str, nargs=1, help='Input processed tally file')
remdefaults.parseargs(parsearg, tempdir=False)
parsearg.add_argument('--outfile', type=str, required=True, help='Output file')
parsearg.add_argument('--force', action='store_true', help='Force if file exists')
parsearg.add_argument('--which', required=True, type=str, choices=['m', 's'], help='Choose m for mean or s for std dev')
parsearg.add_argument('--nocheck', action='store_true', help='Do not check dimensions of array"')

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
tfile = resargs['tfile'][0]
outfile = resargs['outfile']
force = resargs['force']
which = resargs['which']
nocheck = resargs['nocheck']

tfile = remdefaults.libfile(miscutils.addsuffix(tfile, '.npy'))
outfile = remdefaults.libfile(miscutils.addsuffix(outfile, '.npy'))

if os.path.exists(outfile) and not force:
    print("Will not overwrite existing", outfile, "use --force if needed", file=sys.stderr)
    sys.exit(10)

try:
    pfile = np.load(tfile)
except OSError as e:
    print("Problem with file", tfile, "error was", e.args[1], file=sys.stderr)
    sys.exit(11)

if not nocheck and pfile.shape != (3, 2048, 2048):
    print("Expecting processed tally file", tfile, "to be 3x2048x2048", file=sys.stderr)
    sys.exit(12)

counts, meand, sdds = pfile

if which == 's':
    result = sdds
else:
    result = meand

fresult = result.flatten()
fresult = fresult[counts.flatten() != 0]
print("Result min= %.6g max %.6g mean %.6g stdd %.6g" % (fresult.min(), fresult.max(), fresult.mean(), fresult.std()))

np.save(outfile, result)
