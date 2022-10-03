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
remdefaults.parseargs(parsearg)
parsearg.add_argument('--outfile', type=str, required=True, help='Output file - 0th plane mean, 1st plane sd dev')
parsearg.add_argument('--force', action='store_true', help='Force if file exists')

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
tfile = resargs['tfile'][0]
outfile = resargs['outfile']
force = resargs['force']

tfile = miscutils.addsuffix(remdefaults.libfile(tfile), '.npy')
outfile = miscutils.addsuffix(remdefaults.libfile(outfile), '.npy')

if os.path.exists(outfile) and not force:
    print("Will not overwrite existing", outfile, "use --force if needed", file=sys.stderr)
    sys.exit(10)

try:
    tally = np.load(tfile)
except OSError as e:
    print("Problem with file", tfile, "error was", e.args[1], file=sys.stderr)
    sys.exit(11)

if tally.shape != (3, 2048, 2048):
    print("Expecting tally file", tfile, "to be 3x2048x2048", file=sys.stderr)
    sys.exit(12)

counts, sums, sumsq = tally

means = sums / counts
vars = sumsq / counts - means ** 2
sdds = np.sqrt(vars)

result = np.array([counts, means, sdds])

result[np.isnan(result)] = 0
np.save(outfile, result)
