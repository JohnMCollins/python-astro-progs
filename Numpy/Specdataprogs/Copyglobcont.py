#! /usr/bin/env python

# This is for copying the global normalisation when we add extra spectral points and don't want to redo the global normalisation.

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
import simbad
import doppler

parsearg = argparse.ArgumentParser(description='Batch mode copy global continuum', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('infofiles', type=str, help='Specinfo file - in out', nargs=2)
parsearg.add_argument('--force', action='store_true', help='OK to overwrite existing global continuum')

resargs = vars(parsearg.parse_args())

infile, outfile = resargs['infofiles']
force = resargs['force']

if not os.path.isfile(infile):
    infile = miscutils.replacesuffix(infile, specinfo.SUFFIX)
if not os.path.isfile(outfile):
    outfile = miscutils.replacesuffix(outfile, specinfo.SUFFIX)

try:
    inf = specinfo.SpecInfo()
    inf.loadfile(infile)
    iclist = inf.get_ctrlfile()
except specinfo.SpecInfoError as e:
    sys.stdout = sys.stderr
    print "Cannot load info file", infile
    print "Error was:", e.args[0]
    sys.exit(100)
    
try:
    outf = specinfo.SpecInfo()
    outf.loadfile(outfile)
    oclist = outf.get_ctrlfile()
except specinfo.SpecInfoError as e:
    sys.stdout = sys.stderr
    print "Cannot load info file", outfile
    print "Error was:", e.args[0]
    sys.exit(101)

if oclist.yoffset is not None and not force:
    sys.stdout = sys.stderr
    print "Will not overwrite existing global continuum polynomial"
    sys.exit(102)

if iclist.yoffset is None:
    sys.stdout = sys.stderr
    print "Source file", infile, "has no global continuum polynomial"
    sys.exit(103)

oclist.reset_indiv_y()
oclist.yoffset = iclist.yoffset
for n, ic in enumerate(iclist.datalist):
    oclist.datalist[n].yoffset = ic.yoffset

 # Now save result
 
try:
    outf.savefile()
except specinfo.SpecInfoError as e:
    sys.stdout = sys.stderr
    print "Cannot re-save", infofile
    print "Error was", e.args[0]
    sys.exit(150)

sys.exit(0)
