#! /usr/bin/env python

import sys
import os
import os.path
import locale
import argparse
import xml.etree.ElementTree as ET
import miscutils
import xmlutil
import specdatactrl
import datarange

parsearg = argparse.ArgumentParser(description='Init spectrum data files (batch mode)')
parsearg.add_argument('obsdir', type=str, help='Directory of obs data', nargs=1)
parsearg.add_argument('--cdir', type=str, help='Directory for control files (if not CWD')
parsearg.add_argument('--force', action='store_true', help='Force overwrite existing files')

res = vars(parsearg.parse_args())

resdir = res['cdir']
if resdir is None:
    resdir = os.getcwd()
else:
    resdir = os.path.abspath(resdir)
    if not os.path.isdir(resdir):
        sys.stdout = sys.stderr
        print resdir, "directory does not exist"
        sys.exit(100)

srcdir = res['obsdir'][0]

if not os.path.isdir(srcdir):
    sys.stdout = sys.stderr
    print srcdir, "source directory does not exist"
    sys.exit(101)

srcdir = os.path.abspath(srcdir)
sname = os.path.basename(srcdir)

outctrlfle = os.path.join(resdir, sname + '.sac')
outrngfle = os.path.join(resdir, sname + '.spcr')

if not res['force'] and (os.path.exists(outctrlfle) or os.path.exists(outrngfle)):
    sys.stdout = sys.stderr
    print "will not overwrite existing files"
    sys.exit(102)

try:
    currentlist = specdatactrl.SpecDataList(srcdir)
except specdatactrl.SpecDataError as e:
    sys.stdout = sys.stderr
    print "Cannot select obs directory", sname, "-", e.args[0]
    sys.exit(1)
if len(currentlist.obsfname) == 0:
    sys.stdout = sys.stderr
    print "Cannot discover obs file in", sname
    sys.exit(2)
try:
    currentlist.loadfile()
except specdatactrl.SpecDataError as e:
    sys.stdout = sys.stderr
    print "Cannot load/parse files", sname, "-", e.args[0]
    sys.exit(3)    
try:
    specdatactrl.Save_specctrl(outctrlfle, currentlist)
except specdatactrl.SpecDataError as e:
    sys.stdout = sys.stderr
    print "Save control file error", e.args[0]
    sys.exit(103)

rlist = datarange.init_default_ranges()
try:
    datarange.save_ranges(outrngfle, rlist)
except datarange.DataRangeError as e:
    sys.stdout = sys.stderr
    print "Range save error", e.args[0]
    sys.exit(104)
