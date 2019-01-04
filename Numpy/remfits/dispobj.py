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

parsearg = argparse.ArgumentParser(description='Display field from FITS header',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', type=str, nargs='+', help='List of FITS files')
parsearg.add_argument('--field', type=str, help='Field to display', default='OBJECT')
parsearg.add_argument('--plusfn', action='store_true', help='Prepend file names')
parsearg.add_argument('--list', action='store_true', help='List field names in each file')

resargs = vars(parsearg.parse_args())

whichobj = resargs['field']
plusfn = resargs['plusfn']
listf = resargs['list']

errors = 0

if listf:
    for file in resargs['files']:
        try:
            ff = fits.open(file)
        except IOError as e:
            sys.stdout = sys.stderr
            if len(e.args) == 1:
                print("Incorrect format fits file", file)
            else:
                print("Cannot open:", file, "Error was:", e.args[1])
            sys.stdout = sys.__stdout__
            errors += 1
            continue
        h = ff[0].header
        ks = list(h.keys())
        ks.sort()
        print(file + ':')
        for k in ks:
            print("\t" + k + "\t=\t" + str(h[k]))
else:
    for file in resargs['files']:
        try:
            ff = fits.open(file)
        except IOError as e:
            sys.stdout = sys.stderr
            if len(e.args) == 1:
                print("Incorrect format fits file", file)
            else:
                print("Cannot open:", file, "Error was:", e.args[1])
            sys.stdout = sys.__stdout__
            errors += 1
            continue
        h = ff[0].header
        try:
            t = h[whichobj]
            if plusfn:
                print(file + ':', end=' ')
            print(t)
        except KeyError:
            sys.stdout = sys.stderr
            print("Could not find", whichobj, "in fits file", file)
            sys.stdout = sys.__stdout__
            errors += 1
        ff.close()

if errors > 0:
    sys.exit(1)
sys.exit(0)
