#!  /usr/bin/env python3

from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
from astropy.io import fits
from astropy.time import Time
import datetime
import numpy as np
import argparse
import warnings
import sys
import miscutils
import remdefaults
import os.path
import obj_locations
import find_results
import match_finds

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

parsearg = argparse.ArgumentParser(description='Match locations of objects within image and find object results', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', nargs='+', type=str, help='Location file and find results file (or just one if same name)')
remdefaults.parseargs(parsearg, tempdir=False)
parsearg.add_argument('--threshold', type=float, default=20.0, help='Threshold for match in arcsec')
parsearg.add_argument('--verbose', action='store_true', help='Give statistics')

resargs = vars(parsearg.parse_args())
files = resargs['files']
remdefaults.getargs(resargs)
threshold = resargs['threshold']
verbose = resargs['verbose']

locfile = files[0]
if len(files) > 1:
    if len(files) > 2:
        print("Only expecting at most two files", file=sys.stderr)
        sys.exit(10)
    findresfile = files[1]
else:
    findresfile = locfile + ""  # Forces new copy

locations = obj_locations.load_objlist_from_file(locfile)
findres = find_results.load_results_from_file(findresfile)

try:
    matchlist = match_finds.allocate_locs(locations, findres, threshold)
except match_finds.FindError as e:
    print("Match gave error". e.args[0], file=sys.stderr)
    sys.exit(200)

locr = locations.resultlist
findr = findres.resultlist

for row, col, dist in matchlist:
    f = findr[col]
    l = locr[row]
    f.name = l.name
    f.dispname = l.dispname
    f.istarget = l.istarget

findres.reorder()
findres.relabel()
find_results.save_results_to_file(findres, findresfile, True)

if verbose:
    n = nfound = 0
    for f in findres.results():
        n += 1
        if len(f.name) != 0:
            nfound += 1
    print(nfound, "found out of", n, file=sys.stderr)
