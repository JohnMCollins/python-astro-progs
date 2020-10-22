#!  /usr/bin/env python3

import remdefaults
import argparse
import sys
import os.path
import numpy as np
import warnings
import arrayfiles

# Cope with divisions by zero

warnings.simplefilter('ignore', RuntimeWarning)

parsearg = argparse.ArgumentParser(description=' Make bad pixel mask from mean/std deviation file', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('msfile', type=str, nargs=1, help='Input mean std deviation file')
remdefaults.parseargs(parsearg, tempdir=False, database=False)
parsearg.add_argument('--outfile', type=str, help='Output bad pixel mask default is same prefix as input')
parsearg.add_argument('--force', action='store_true', help='Force if file exists')
parsearg.add_argument('--meangt', type=float, help='Mark as bad pixels with means this times greater than this')
parsearg.add_argument('--stdgt', type=float, help='Mark as bad pixels with standard deviations greater than this')

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
msfile = resargs['msfile'][0]
outfile = resargs['outfile']
force = resargs['force']
meangt = resargs['meangt']
stdgt = resargs['stdgt']

if meangt is None and stdgt is None:
    print("Must put either --meangt or --stdgt values", file=sys.stderr)
    sys.exit(5)

try:
    inputfile, sourcearray = arrayfiles.get_argfile(msfile)
except arrayfiles.ArrayFileError as e:
    print("Trouble with source file", e.args[0], file=sys.stderr)
    sys.exit(10)

if outfile is None:
    outfile = inputfile
outfile = remdefaults.bad_pixmask(outfile)

if os.path.exists(outfile) and not force:
    print("Will not overwrite existing", outfile, "use --force if needed", file=sys.stderr)
    sys.exit(11)

flatarray = sourcearray.flatten()
flatarray = flatarray[flatarray != 0]
meanresult = None
stdresult = None
if meangt is not None:
    thresh = meangt * flatarray.mean()
    if thresh < 0:
        meanresult = (sourcearray < -thresh) & (sourcearray != 0.0)
    else:
        meanresult = sourcearray > thresh
if stdgt is not None:
    thresh = abs(stdgt) * flatarray.std() + flatarray.mean()
    stdresult = sourcearray > thresh
if meanresult is None:
    result = stdresult
elif stdresult is None:
    result = meanresult
else:
    result = meanresult | stdresult

try:
    outf = open(outfile, 'wb')
except OSError as e:
    print("Could not open", outfile, "error was", e.args[1], file=sys.stderr)
    sys.exit(50)

np.save(outf, result)
outf.close()
print("There were", np.count_nonzero(result), "in bad pixel mask out of", np.count_nonzero(flatarray), file=sys.stderr)
sys.exit(0)
