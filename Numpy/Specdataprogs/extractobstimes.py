#! /usr/bin/env python

import sys
import os
import os.path
import string
import locale
import argparse
import numpy as np
import miscutils
import specdatactrl
import datarange
import specinfo
import equivwidth
import meanval

parsearg = argparse.ArgumentParser(description='Extract obs times from info file')
parsearg.add_argument('infofile', type=str, help='Specinfo file', nargs=1)
parsearg.add_argument('--outfile', type=str, help='Output file if not stdout')

resargs = vars(parsearg.parse_args())

infofile = resargs['infofile'][0]
outfile = resargs['outfile']

if not os.path.isfile(infofile):
    infofile = miscutils.replacesuffix(infofile, specinfo.SUFFIX)

try:
    inf = specinfo.SpecInfo()
    inf.loadfile(infofile)
    ctrllist = inf.get_ctrlfile()
except specinfo.SpecInfoError as e:
    sys.stdout = sys.stderr
    print "Cannot load info file", infofile
    print "Error was:", e.args[0]
    sys.exit(100)

if outfile is not None:
    try:
        outf = open(outfile, 'w')
    except IOError as e:
        sys.stdout = sys.stderr;
        print "Cannot open output file", outfile
        print "Error was:", e.args[1]
        sys.exit(100)
    sys.stdout = outf

print len(ctrllist.datalist), 1, 1
for datum in ctrllist.datalist:
    print "%#.16g" % datum.modbjdate

sys.exit(0)
