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
import math
import remdefaults
import remfits
import os.path
import find_results

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

parsearg = argparse.ArgumentParser(description='List contents of find results ', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', nargs='+', type=str, help='Find results file or files')
remdefaults.parseargs(parsearg, tempdir=False, database=False)

resargs = vars(parsearg.parse_args())
files = resargs['files']
remdefaults.getargs(resargs)

for frfile in files:
    fullfile = remdefaults.libfile(frfile)
    try:
        rstr = find_results.load_results_from_file(fullfile)
    except find_results.FindResultErr as e:
        print(frfile, "error -", e.args[0], file=sys.stderr)
        continue
    print(frfile, end='')
    if rstr.obsdate is not None:
        print(rstr.obsdate.strftime(" Based on observation %d/%m/%Y @ %H:%M:%S"), end='')
    print(":\n")

    names = []
    for r in rstr.results():
        if len(r.name) != 0:
            names.append(r.name)
        else:
            names.append(r.label)
    nsize = max((len(p) for p in names))
    pnames = [x + " " * (nsize - len(x)) for x in names]
    for n, r in zip(pnames, rstr.results()):
        print("{name} {ra:8.3f} {dec:8.3f} {ap:3n} {adu:10.2f}".format(name=n, ra=r.radeg, dec=r.decdeg, ap=r.apsize, adu=r.adus), end='')
        if r.istarget:
            print(" (target)", end='')
        print()
