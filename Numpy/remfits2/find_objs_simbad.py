#!  /usr/bin/env python3

from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
from astropy.io import fits
from astropy.time import Time
from astroquery.simbad import Simbad
from astropy.coordinates import SkyCoord, Angle
import astropy.units as u
import datetime
import numpy as np
import argparse
import warnings
import sys
import miscutils
import math
import remdefaults
import remfits
import os.path
import find_results

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

parsearg = argparse.ArgumentParser(description='Put object names in find results', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('file', nargs=1, type=str, help='Find results file')
remdefaults.parseargs(parsearg, tempdir=False, database=False)
parsearg.add_argument('--radius', type=float, default=2.0, help='Search radius in arcmin')

resargs = vars(parsearg.parse_args())
resfile, = resargs['file']
remdefaults.getargs(resargs)
radius = resargs['radius']

try:
    rstr = find_results.load_results_from_file(resfile)
except find_results.FindResultErr as e:
    print("Open of", resfile, "gave error", e.args[0], file=sys.stderr)
    if resargs['inlib']:
        print("Did you forget to put --inlib in to stop searching library", file=sys.stderr)
    sys.exit(100)

sb = Simbad()

changes = 0
for r in rstr.results():
    sres = sb.query_region(SkyCoord(ra=r.radeg * u.deg, dec=r.decdeg * u.deg), radius=radius * u.arcmin)
    if sres is None:
        continue
    r.name = sres[0]['MAIN_ID'].decode()
    changes += 1

if changes != 0:
    print(changes, "changed", file=sys.stderr)
    find_results.save_results_to_file(rstr, resfile, force=True)
