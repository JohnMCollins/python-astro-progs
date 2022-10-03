#! /usr/bin/env python

"""Extract times and flux from K2 files from MAST"""

import sys
import argparse
import os
import os.path
import math
import numpy as np
from astropy.time import Time
from astropy.io import fits
import miscutils

parsearg = argparse.ArgumentParser(description='Extract time/flux data from K2 data from MAST files', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('file', nargs=1, type=str, help='FITS file to process')
parsearg.add_argument('--outfile', type=str, help='Output file name if not source with .txt')
parsearg.add_argument('--force', action='store_true', help="Force overwrite of existing output file")

resargs = vars(parsearg.parse_args())
input_file = resargs['file'][0]
output_file = resargs['outfile']
force = resargs['force']

if output_file is None:
    output_file = miscutils.replacesuffix(input_file, 'txt')

if not force and os.path.exists(output_file):
    print(output_file, "exists, use --force if needed", file=sys.stderr)
    sys.exit(10)

try:
    ff = fits.open(input_file)
except OSError as e:
    print("Cannot open", input_file, "error was", e.args[1], file=sys.stderr)
    sys.exit(11)

fdat = ff[1].data
fhdr = ff[1].header
try:
    results = np.array([(t, fl, fle) for t, fl, fle in zip(fdat.field('TIME'), fdat.field('SAP_FLUX'), fdat.field('SAP_FLUX_ERR')) if not math.isnan(fl)])
except KeyError as e:
    print("Parsing array gave error", e.args[0], file=sys.stderr)
    sys.exit(20)

try:
    bjdref = fhdr['BJDREFI'] + fhdr['BJDREFF']
except KeyError:
    print("Cannot find ref date", file=sys.stderr)
    sys.exit(21)

t = Time(bjdref + results[0].min(), format='jd')
print("Ref date is {:.12f} corresponding to {:%d/%m/%Y}".format(t.jd, t.datetime))
np.savetxt(output_file, results)
