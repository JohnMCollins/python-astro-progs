#! /usr/bin/env python

import sys
import os
import os.path
import string
import argparse
import numpy as np

acol = dict(ew = 1, ps = 2, pr = 3)

def parsefarg(arg):
    """Parse file:column arg"""
    arg = string.replace(arg, ',', ':')
    try:
        filename, col = string.split(arg, ':')
        if not os.path.isfile(filename):
            print "Cannot find file", filename
            sys.exit(11)
        col = string.lower(col)
        if col in acol:
            return (filename, acol[col])
        col = int(col)
        if col < 1 or col > 3:
            print "Invalid column", col, "should be 1 2 or 3"
        return (filename, col)
    except (ValueError, TypeError):
        print "Cannot understand argument", arg
        sys.exit(12)  

parsearg = argparse.ArgumentParser(description='Merge EW file columns', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('ewfiles', type=str, help='File1:field File2:field File3:field Outfile', nargs=4)
parsearg.add_argument('--force', action='store_true', help='OK to overwrite existing output file')
parsearg.add_argument('--checkdates', action='store_false', help='Check dates line up')

resargs = vars(parsearg.parse_args())

f1, f2, f3, outfile = resargs['ewfiles']

if not resargs['force'] and os.path.isfile(outfile):
    print "Will not overwrite existing", outfile
    sys.exit(10)

file1, col1 = parsefarg(f1)
file2, col2 = parsefarg(f2)
file3, col3 = parsefarg(f3)

inf = []
for f in (file1, file2, file3):
    try:
        inf.append(np.loadtxt(f, unpack=True))
    except ValueError:
        print f, "does not look like an EW file"
        sys.exit(12)
        
inf1, inf2, inf3 = inf

if inf1.shape != inf2.shape or inf2.shape != inf3.shape:
    print "Sorry shapes of files do not line un"
    print file1, "is shape", inf1.shape
    print file2, "is shape", inf2.shape
    print file3, "is shape", inf3,shape
    sys.exit(13)
    
if resargs['checkdates']:
    if np.count_nonzero(inf1[1] != inf2[1]):
        print "Dates in", file1, "do not match dates in", file2
        sys.exit(14)
    if np.count_nonzero(inf1[1] != inf3[1]):
        print "Dates in", file1, "do not match dates in", file3
        sys.exit(14)

outarray = inf1.copy()
outarray[2] = inf1[col1*2]
outarray[3] = inf1[col1*2+1]
outarray[4] = inf2[col2*2]
outarray[5] = inf2[col2*2+1]
outarray[6] = inf3[col3*2]
outarray[7] = inf3[col3*2+1]

np.savetxt(outfile, outarray.transpose())
sys.exit(0)
