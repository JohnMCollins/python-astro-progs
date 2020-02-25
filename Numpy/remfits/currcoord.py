#! /usr/bin/env python3

from astropy.io import fits
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
import astroquery.utils as autils
import numpy as np
import argparse
import sys
import string
import objcoord
import warnings
import datetime

parsearg = argparse.ArgumentParser(description='Get coords for date', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('file', type=str, nargs='+', help='FITS files (takes date from first)')
parsearg.add_argument('--outfile', type=str, required=True, help='Output file')
parsearg.add_argument('--objects', nargs='+', type=str, help='Object IDs to use')

resargs = vars(parsearg.parse_args())
ffnames = resargs['file']

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)
autils.suppress_vo_warnings()

ffile = fits.open(ffnames[0])
ffhdr = ffile[0].header

odt = datetime.datetime.now()
for dfld in ('DATE-OBS', 'DATE', '_ATE'):
    if dfld in ffhdr:
        odt = ffhdr[dfld]
        break

objids = resargs['objects']
outfile = resargs['outfile']

resarray = []

errors = 0

for obj in objids:

    coords = objcoord.objcurrcoord(obj, odt)

    if coords is None:
        print("Cannot find object id " + obj, file=sys.stderr)
        errors += 1
        continue

    resarray.append(coords)

if errors != 0:
    print("Aborting", file=sys.stderr)
np.savetxt(outfile, resarray)
