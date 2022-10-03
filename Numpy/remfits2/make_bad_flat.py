#!  /usr/bin/env python3

"""Make badpix mask from master flat file"""

import argparse
import sys
import os.path
import warnings
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
import numpy as np
import remdefaults
import remfits

# Cope with divisions by zero

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)
warnings.simplefilter('ignore', RuntimeWarning)

parsearg = argparse.ArgumentParser(description=' Make bad pixel mask from master flat file', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('ffile', type=str, nargs=1, help='Input master flat file')
remdefaults.parseargs(parsearg, tempdir=False, database=False)
parsearg.add_argument('--outfile', type=str, help='Output bad pixel mask default is same prefix as input')
parsearg.add_argument('--create', action='store_true', help='Create new file, otherwise update existing')
parsearg.add_argument('--force', action='store_true', help='Force if file exists and creating new')
parsearg.add_argument('--verbose', action='store_true', help='Summaries result')
parsearg.add_argument('--minvalue', type=float, default=0.75, help='Value of flat field element to reject')
parsearg.add_argument('--trim', type=int, default=100, help='Amount to trim off edges')
parsearg.add_argument('--toomany', type=float, default=10.0, help='Percent regarded as too many')

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
ffile = resargs['ffile'][0]
outfile = resargs['outfile']
creating = resargs['create']
force = resargs['force']
verbose = resargs['verbose']
minvalue = resargs['minvalue']
trim = resargs['trim']
toomany = resargs['toomany']

try:
    inputfile = remfits.parse_filearg(ffile, None)
except remfits.RemFitsErr as e:
    print("Could not open", ffile, "error was", e.args[0], file=sys.stderr)
    sys.exit(10)

if outfile is None:
    outfile = ffile

outfile = remdefaults.bad_pixmask(outfile)

existingbpm = None

if os.path.exists(outfile):
    if creating:
        if not force:
            print("Will not recreate existing", outfile, "use --force if needed", file=sys.stderr)
            sys.exit(11)
    else:
        try:
            existingbpm = np.load(outfile)
        except OSError as e:
            print("Could not load", outfile, "error was", e.args[1], file=sys.stderr)
            sys.exit(12)
elif not creating:
    print(outfile, "does not exist, use --create if needed", file=sys.stderr)
    sys.exit(13)

inputdata = inputfile.data
startx, starty, endx, endy = inputfile.dims()
if trim > 0:
    inputdata = inputdata[trim:-trim, trim:-trim]
    if inputdata.size == 0:
        print("Trim of", trim, "is too much size is", endx - startx, "by", endy - starty, file=sys.stderr)
        sys.exit(12)
    startx += trim
    starty += trim
    endx -= trim
    endy -= trim

maskf = inputdata < minvalue
nnz = np.count_nonzero(maskf)
if nnz / maskf.size >= toomany / 100.0:
    print("Too many in BP mask", nnz, "out of", maskf.size, "accepting up to", toomany, "percent", file=sys.stderr)
    sys.exit(12)
result = np.zeros((2048, 2048), dtype=bool)
result[starty:endy, startx:endx] = maskf
rnz = np.count_nonzero(result)
if rnz == 0:
    if verbose:
        print("No bad pixels in result")
    if not creating:
        sys.exit(0)
elif verbose:
    if existingbpm is not None:
        enz = np.count_nonzero(existingbpm)
    else:
        enz = 0
    if rnz != 0:
        print(rnz, "bad pixels in result")
    if enz == 0:
        print("Nothing previous")
    else:
        print(enz, "bad pixels before")
        if rnz != 0:
            comm = result & existingbpm
            print(np.count_nonzero(comm), "in common")

if existingbpm is not None:
    result |= existingbpm

try:
    outf = open(outfile, 'wb')
except OSError as e:
    print("Could not open", outfile, "error was", e.args[1], file=sys.stderr)
    sys.exit(50)

np.save(outf, result)
outf.close()
sys.exit(0)
