#! /usr/bin/env python

import sys
import os
import os.path
import string
import argparse
import numpy as np

parsearg = argparse.ArgumentParser(description='Merge file columns', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('--outfile', type=str, required=True, help='Result file')
parsearg.add_argument('infiles', type=str, help='File1:fields ...', nargs='+')
parsearg.add_argument('--force', action='store_true', help='OK to overwrite existing output file')
parsearg.add_argument('--checkdates', action='store_false', help='Check dates line up')
parsearg.add_argument('--datecol', type=int, default=1, help='Column in source for BJD')

resargs = vars(parsearg.parse_args())

outfile = resargs['outfile']
forceout = resargs['force']
checkdate = resargs['checkdates']
datecol = resargs['datecol'] - 1

if not forceout and os.path.isfile(outfile):
    print "Will not overwrite existing", outfile
    sys.exit(10)

infiles = dict()
infields = []
errors = 0

for filearg in resargs['infiles']:
    try:
        fbits = string.split(filearg, ':')
        if len(fbits) == 1:
            inf = filearg
            cols = [1]
        else:
            inf, cnames = fbits
            cols = map(lambda x: int(x), string.split(cnames,','))
        for col in cols:
            infields.append((inf, col-1))
        infiles[inf] = 1
    except ValueError:
        print "Could not understand", fileaarg
        errors += 1

if errors > 0:
    sys.exit(11)

fnames = infiles.keys()

for inf in fnames:
    try:
        infiles[inf] = np.loadtxt(inf, unpack=True)
    except IOError as e:
        print "Cannot laad", inf, "Error was", e.args[1]
        errors += 1

if errors > 0:
    sys.exit(12)

firstf = fnames[0]
firstfsize = infiles[firstf].shape

for inf in fnames:
    s = infiles[inf]
    if len(s.shape) != 2:
        print "Expected", inf, "to be 2 dims but it has", len(s.shape)
        errors += 1
    if s.shape[-1] != firstfsize[-1]:
        print "Differing number of columns in", infields
        errors += 1

if errors > 0:
    print "Sizes of files"
    for inf in fnames:
        print inf, infiles[inf].shape
    sys.exit(13)

if checkdate:
    dates = infiles[firstf][datecol]
    for inf in fnames:
        ndates = infiles[inf][datecol]
        if np.count_nonzero(dates != ndates) != 0:
            print "Dates in", firstf, "different from", inf
            errors += 1

if errors > 0:
    sys.exit(14)

firstres = infields.pop(0)
inf, col = firstres
outarray = infiles[inf][col:col+1]

for fld in infields:
    inf, col = fld
    outarray = np.concatenate((outarray, infiles[inf][col:col+1]))

np.savetxt(outfile, outarray.transpose())
sys.exit(0)
