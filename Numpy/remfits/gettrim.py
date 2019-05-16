#!  /usr/bin/env python3

# @Author: John M Collins <jmc>
# @Date:   2019-01-04T22:45:56+00:00
# @Email:  jmc@toad.me.uk
# @Filename: dispobj.py
# @Last modified by:   jmc
# @Last modified time: 2019-01-04T23:04:36+00:00

from astropy.io import fits
import argparse
import sys
import trimarrays

parsearg = argparse.ArgumentParser(description='Get trim arguments from FITS file usually flat filer',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', type=str, nargs='+', help='List of FITS files')
parsearg.add_argument('--asarg', action='store_true', help='Just give arguments for programs')

resargs = vars(parsearg.parse_args())

asarg = resargs['asarg']

errors = 0

for file in resargs['files']:
    try:
        ff = fits.open(file)
    except IOError as e:
        if len(e.args) == 1:
            print("Incorrect format fits file", file, file=sys.stderr)
        else:
            print("Cannot open:", file, "Error was:", e.args[1], file=sys.stderr)
            errors += 1
        continue
    
    img = trimarrays.trimzeros(trimarrays.trimnan(ff[0].data))
    rows, cols = img.shape
    if asarg:
        print("%d:%d" % (rows, cols))
    else:
        print("%s:\t%4d\t%4d" % (file, rows, cols))
    ff.close()

if errors > 0:
    sys.exit(1)
sys.exit(0)
