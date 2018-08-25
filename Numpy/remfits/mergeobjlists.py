#! /usr/bin/env python

from astropy.io import fits
from astropy import wcs
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
from astropy.time import Time
import astroquery.utils as autils
import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mp
from matplotlib import colors
import argparse
import sys
import datetime
import os.path
import string
import warnings
import miscutils
import remgeom
import remfitsobj

parsearg = argparse.ArgumentParser(description='Merge object finds in fits filess', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('objfiles', type=str, nargs=2, help='REM Fits object files to be mered 2nd one is the target')
parsearg.add_argument('--create', action='store_true', help="Create second file if it doesn't exist, otherwise error")
parsearg.add_argument('--force', action='store_true', help='Force copy of duplicated obs from first file')

resargs = vars(parsearg.parse_args())

srcfile, destfile = resargs['objfiles']
createdest = resargs['create']
forcecopy = resargs['force']

srcobjs = remfitsobj.RemobjSet()
try:
    srcobjs.loadfile(srcfile)
except remfitsobj.RemObjError as e:
    print >>sys.stderr,  "Error loading source file", srcfile, e.args[0]
    sys.exit(30)

target = srcobjs.targname
if target is None:
    print >>sys.stderr, "Source file", srcfile, "does not have target"
    sys.exit(31)

destobjs = remfitsobj.RemobjSet()
try:
    destobjs.loadfile(destfile)
    if destobjs.targname != srcobjs.targname:
        if destobjs.targname is None:
            print >>sys.stderr, "No target in", destfile
        else:
            print >>sys.stderr, "source target is", srcobjs.targname, "dest target is", destobjs.targname
        sys.exit(32) 
except remfitsobj.RemObjError as e:
    if e.warningonly:
        if createdest:
            print >>sys.stderr, "(Warning) creating", destfile
            destobjs.targname = srcobjs.targname
        else:
            print >>sys.stderr, "destination file", destfile, "does not exist"
            sys.exit(33)
    else:
        print >>sys.stderr,  "Error loading file", e.args[0]
        sys.exit(30)

# Get current objects in destobjs - don't need to change directory

dlist = destobjs.getobslist(adjfiles = False)

slist = srcobjs.getobslist()
dups = 0

for ob in slist:
    try:
        destobjs.addobs(ob, forcecopy)
    except remfitsobj.RemObjError:
        dups += 1

if dups != 0:
    print >>sys/stderr. dups, "duplicates found"

destobjs.savefile(destfile)
