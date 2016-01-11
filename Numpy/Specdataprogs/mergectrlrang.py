#! /usr/bin/env python

# Merge ctrl file and range file into info file

import argparse
import os
import os.path
import sys

import miscutils
import specinfo
import specdatactrl
import datarange
import xmlutil

CTRLSUFF = 'sac'
RANGESUFF = 'spcr'

parsearg = argparse.ArgumentParser(description='Merge control file and range file into one', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('--ctrlfile', type=str, help='Input control file')
parsearg.add_argument('--rangefile', type=str, help='Range file')
parsearg.add_argument('--outfile', help='Output file', type=str)
parsearg.add_argument('--force', action='store_true', help='Force overwrite of existing file or outfile without suffix')
parsearg.add_argument('name', type=str, nargs='?', help='Possible common file prefix if nothing else given.')

resargs = vars(parsearg.parse_args())

ctrlfile = resargs['ctrlfile']
rangefile = resargs['rangefile']
outfile = resargs['outfile']
force = resargs['force']

# Try to construct source files out of names given

prefix = resargs['name']
if prefix is not None:
    if ctrlfile is None:
        ctrlfile = miscutils.replacesuffix(prefix, CTRLSUFF)
    if rangefile is None:
        rangefile = miscutils.replacesuffix(prefix, RANGESUFF)
    if outfile is None:
        outfile = miscutils.replacesuffix(prefix, specinfo.SUFFIX)

else:
    # No common name given

    if ctrlfile is None:
        if rangefile is None:
            if outfile is None:
                print "No source files given"
                sys.exit(1)
            else:
                ctrlfile = miscutils.replacesuffix(outfile, CTRLSUFF)
            rangefile = miscutils.replacesuffix(outfile, RANGESUFF)
        else:
            ctrlfile = miscutils.replacesuffix(rangefile, RANGESUFF)
            if outfile is None:
                outfile = miscutils.replacesuffix(rangefile, specinfo.SUFFIX)
    else:
        if rangefile is None:
            rangefile = miscutils.replacesuffix(ctrlfile, RANGESUFF)
        if outfile is None:
            outfile = miscutils.replacesuffix(ctrlfile, specinfo.SUFFIX)

if not os.path.isfile(ctrlfile):
    ctrlfile = miscutils.replacesuffix(ctrlfile, CTRLSUFF)
    if not os.path.isfile(ctrlfile):
        print "Cannot find ctrl file", ctrlfile
        sys.exit(2)

if not os.path.isfile(rangefile):
    rangefile = miscutils.replacesuffix(rangefile, RANGESUFF)
    if not os.path.isfile(rangefile):
        print "Cannot find range file", rangefile
        sys.exit(3)

if not miscutils.hassuffix(outfile, specinfo.SUFFIX):
    if not force:
        print "Expecting outfile", outfile, "to have suffix", specinfo.SUFFIX
        sys.exit(4)

if os.path.exists(outfile) and not force:
    print "Will not overwrite existing", outfile
    sys.exit(5)

try:
    ctrllist = specdatactrl.Load_specctrl(ctrlfile)
except specdatactrl.SpecDataError as e:
    print "Could not load control file", ctrlfile
    print "Error was:"
    print e.args[0]
    sys.exit(6)

try:
    rangelist = datarange.load_ranges(rangefile)
except datarange.DataRangeError as e:
    print "Could not load range file", rangefile
    print "Error was:"
    print e.args[0]
    sys.exit(7)

# OK do the Business

try:
    outlist = specinfo.SpecInfo()
    outlist.set_ctrlfile(ctrllist)
    outlist.set_rangelist(rangelist)
    outlist.savefile(outfile)
except specinfo.SpecInfoError as e:
    print "Could not save output file", outfile
    print "Error was"
    print e.args[0]
    sys.exit(10)
