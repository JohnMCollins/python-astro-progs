#! /usr/bin/env python

# Apply correction to UVES values from figures given.

import sys
import os
import string
import re
import os.path
import argparse
import numpy as np
import miscutils
import specinfo
import specdatactrl
import datarange

SECSPERDAY = 3600.0 * 24.0

parsearg = argparse.ArgumentParser(description='Process UVES data and reset RV from JB correction table', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('--infofile', type=str, help='Input spectral info file', required=True)
parsearg.add_argument('--cfile', type=str, help='File of RV corrections', required=True)
parsearg.add_argument('--add', action='store_true', help='Add corrections instead of subtracting')

resargs = vars(parsearg.parse_args())

infofile = resargs['infofile']
cfile = resargs['cfile']
addit = resargs['add']

# Now read the info file

if not os.path.isfile(infofile):
    infoflle = miscutils.replacesuffix(infofile, specinfo.SUFFIX)

try:
    sinfo = specinfo.SpecInfo()
    sinfo.loadfile(infofile)
    ctrllist = sinfo.get_ctrlfile()
except specinfo.SpecInfoError as e:
    print "Cannot open info file, error was", e.args[0]
    sys.exit(12)

try:
    cdata = np.loadtxt(cfile)       # NB no unpack
except IOError as e:
    print "Cannot read corrections file error was", e.args[0]
    sys.exit(13)

# Grab correction for first one, NB in m/s not km/s

inithv = ctrllist.datalist[0].hvcorrect

if addit:
    for snum, corrn in cdata:
        ctrllist.datalist[int(snum)-1].hvcorrect = inithv + corrn * 1000.0
else:
    for snum, corrn in cdata:
        ctrllist.datalist[int(snum)-1].hvcorrect = inithv - corrn * 1000.0

sinfo.savefile()
