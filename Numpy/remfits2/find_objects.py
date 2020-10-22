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

parsearg = argparse.ArgumentParser(description='Find objects in image ', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', nargs=2, type=str, help='Image file and output find results')
remdefaults.parseargs(parsearg, tempdir=False)
parsearg.add_argument('--force', action='store_true', help='Force overwrite of existing file')
parsearg.add_argument('--significance', type=float, default=10.0, help='Multiples of standard deviation to look for in search')
parsearg.add_argument('--apsize', type=int, default=6, help='Aperature size to search initially"')
parsearg.add_argument('--totsign', type=float, default=1.0, help='Total multiple of std devs for total ADU count to be significant')
parsearg.add_argument('--ignleft', type=int, default=0, help='Amount on left to ignore')
parsearg.add_argument('--ignright', type=int, default=0, help='Amount on right to ignore')
parsearg.add_argument('--igntop', type=int, default=0, help='Amount on top to ignore')
parsearg.add_argument('--ignbottom', type=int, default=0, help='Amount on bottom to ignore')

resargs = vars(parsearg.parse_args())
infile, outfile = resargs['files']
remdefaults.getargs(resargs)
force = resargs['force']
signif = resargs['significance']
apsize = resargs['apsize']
totsign = resargs['totsign']
outfile = remdefaults.libfile(outfile)
ignleft = resargs['ignleft']
ignright = resargs['ignright']
igntop = resargs['igntop']
ignbottom = resargs['ignbottom']

mydb, dbcurs = remdefaults.opendb()

try:
    inputfile = remfits.parse_filearg(infile, dbcurs)
except remfits.RemFitsErr as e:
    print(e.args[0], file=sys.stderr)
    sys.exit(52)

rstr = find_results.FindResults(inputfile)

if rstr.findfast(sign=signif, apwidth=apsize, totsign=totsign, ignleft=ignleft, ignright=ignright, igntop=igntop, ignbottom=ignbottom) == 0:
    print("No results found", file=sys.stderr)
    sys.exit(1)

try:
    find_results.save_results_to_file(rstr, outfile, force)
except find_results.FindResultErr as e:
    print(e.args[0], file=sys.stderr)
    sys.exit(100)
