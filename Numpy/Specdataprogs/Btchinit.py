#! /usr/bin/env python

import sys
import os
import os.path
import locale
import argparse
import specdatactrl
import datarange
import specinfo
import simbad
import miscutils

parsearg = argparse.ArgumentParser(description='Init spectrum data files (batch mode)')
parsearg.add_argument('obsdir', type=str, help='Directory of obs data', nargs=1)
parsearg.add_argument('--cdir', type=str, help='Directory for control files (if not CWD')
parsearg.add_argument('--obsfile', type=str, help='Location of obs file name in case it is not clear')
parsearg.add_argument('--force', action='store_true', help='Force overwrite existing files')
parsearg.add_argument('--objname', type=str, help='Object name if not same as obs data')
parsearg.add_argument('--simbadrv', action='store_true', help='Initialise RV from SIMBAD')
parsearg.add_argument('--rv', type=float, help='Specify RV to uses')

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

outinffile = os.path.join(resdir, miscutils.addsuffix(sname, specinfo.SUFFIX))

if not res['force'] and os.path.exists(outinffile):
    sys.stdout = sys.stderr
    print "will not overwrite existing files"
    sys.exit(102)

try:
    currentlist = specdatactrl.SpecDataList(srcdir, cols = ('modbjdate', 'hvcorrect', 'yerror'))
except specdatactrl.SpecDataError as e:
    sys.stdout = sys.stderr
    print "Cannot select obs directory", sname, "-", e.args[0]
    sys.exit(1)
if res['obsfile'] is not None:
    currentlist.obsfname = os.path.abspath(res['obsfile'])
    if not os.path.isfile(currentlist.obsfname):
        sys.stdout = sys.stderr
        print "Cannot open obs file", currentlist.obsfname
        sys.exit(10)
if len(currentlist.obsfname) == 0:
    sys.stdout = sys.stderr
    print "Cannot discover obs file in", sname, "please specify with --obsfile"
    sys.exit(2)
try:
    currentlist.loadfile()
except specdatactrl.SpecDataError as e:
    sys.stdout = sys.stderr
    print "Cannot load/parse files", sname, "-", e.args[0]
    sys.exit(3)

objname = res['objname']
if objname is not None:
    currentlist.objectname = objname
else:
    objname = currentlist.objectname

if res['simbadrv']:
    rv = simbad.getrv(objname)
    if rv is None:
        sys.stdout = sys.stderr
        print "Sorry cannot find RV from SIMBAD for", objname
        sys.exit(11)
    currentlist.rvcorrect = rv
elif res['rv'] is not None:
    currentlist.rvcorrect = res['rv']

rlist = datarange.init_default_ranges()
try:
    sinf = specinfo.SpecInfo()
    sinf.set_ctrlfile(currentlist)
    sinf.set_rangelist(rlist)
    sinf.savefile(outinffile)
except specinfo.SpecInfoError as e:
    sys.stdout = sys.stderr
    print "Could not save output file", outinffile
    print "Error was"
    print e.args[0]
    sys.exit(104)
