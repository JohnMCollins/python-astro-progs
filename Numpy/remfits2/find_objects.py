#!  /usr/bin/env python3

"""Find objects in image"""

import argparse
import warnings
import sys
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
import remdefaults
import remfits
import find_results

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

parsearg = argparse.ArgumentParser(description='Find objects in image ', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', nargs='+', type=str, help='Image file and output find results')
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
flist = resargs['files']
if len(flist) == 1:
    infile = outfile = flist[0]
else:
    try:
        infile, outfile = flist
    except ValueError:
        print("Expecting one or two file arguments not", ", ".join(flist))
        sys.exit(50)
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
