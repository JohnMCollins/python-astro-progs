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

parsearg = argparse.ArgumentParser(description='Make mean and standard deviations from tally', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('tfile', type=str, nargs=1, help='Input tally file"')
remdefaults.parseargs(parsearg, tempdir=False, database=False)
parsearg.add_argument('--outfile', type=str, help='Output file - 0th plane mean, 1st plane sd dev use same name as input if not given')
parsearg.add_argument('--force', action='store_true', help='Force if file exists')
parsearg.add_argument('--nocheck', action='store_true', help='Do not check dimensions of array"')

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
ptfile = resargs['tfile'][0]
outfile = resargs['outfile']
force = resargs['force']
nocheck = resargs['nocheck']

tfile = remdefaults.tally_file(ptfile)
if outfile is None:
    outfile = ptfile
outfile = remdefaults.meanstd_file(outfile)

if os.path.exists(outfile) and not force:
    print("Will not overwrite existing", outfile, "use --force if needed", file=sys.stderr)
    sys.exit(10)

try:
    tally = np.load(tfile)
except OSError as e:
    print("Problem with file", tfile, "error was", e.args[1], file=sys.stderr)
    sys.exit(11)

if not nocheck and tally.shape != (5, 2048, 2048):
    print("Expecting tally file", tfile, "to be 5x2048x2048", file=sys.stderr)
    sys.exit(12)

counts, sums, sumsq, mins, maxes = tally

means = sums / counts
vars = sumsq / counts - means ** 2
sdds = np.sqrt(vars)

result = np.array([counts, means, sdds, mins, maxes])

result[np.isnan(result)] = 0
outf = open(outfile, "wb")
np.save(outf, result)
outf.close()
