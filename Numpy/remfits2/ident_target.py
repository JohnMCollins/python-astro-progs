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
import dbobjinfo

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

parsearg = argparse.ArgumentParser(description='Find target in find results ', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', nargs=2, type=str, help='Image file and find results')
remdefaults.parseargs(parsearg, tempdir=False)

resargs = vars(parsearg.parse_args())
infile, resfile = resargs['files']
remdefaults.getargs(resargs)
resfile = remdefaults.libfile(resfile)

mydb, dbcurs = remdefaults.opendb()

try:
    inputfile = remfits.parse_filearg(infile, dbcurs)
except remfits.RemFitsErr as e:
    print("open of image file", infile, "gave error", e.args[0], file=sys.stderr)
    sys.exit(52)

try:
    rstr = find_results.load_results_from_file(resfile, inputfile)
except find_results.FindResultErr as e:
    print("open of results file", resfile, "gave error", e.args[0], file=sys.stderr)
    sys.exit(100)

targname = inputfile.target
if targname is None:
    print("No target in", infile, file=sys.stderr)
    sys.exit(101)

ntarg = dbobjinfo.get_targetname(dbcurs, targname)
if ntarg != targname:
    print("Taking", targname, "as", ntarg, file=sys.stderr)
    targname = ntarg

targobs = dbobjinfo.get_object(dbcurs, targname)

targra = targobs.get_ra(inputfile.date)
targdec = targobs.get_dec(inputfile.date)
print(targname, "ra", targra, "dec", targdec, "in file", inputfile.hdr['RA'], inputfile.hdr['DEC'])

targres = None
targdistsq = 1e20
targn = -99

n = 0

for res in rstr.results():
    distsq = (res.radeg - targra) ** 2 + (res.decdeg - targdec) ** 2
    print("obj", n, "ra", res.radeg, "dec", res.decdeg, "dist", math.sqrt(distsq))
    n += 1
    if distsq < targdistsq:
        targdistsq = distsq
        targres = res
        targn = n
