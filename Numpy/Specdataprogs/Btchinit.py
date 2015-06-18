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
import specinfo
import simbad
import doppler

parsearg = argparse.ArgumentParser(description='Init spectrum data files (batch mode)')
parsearg.add_argument('obsdir', type=str, help='Directory of obs data', nargs=1)
parsearg.add_argument('--cdir', type=str, help='Directory for control files (if not CWD')
parsearg.add_argument('--force', action='store_true', help='Force overwrite existing files')
parsearg.add_argument('--simbadrv', type=str, help='Adjust by ')
parsearg.add_argument('--peakname', type=str, default='halpha', help='Name of range for peak to select')
parsearg.add_argument('--peakdescr', type=str, default='H Alpha peak', help='Description of peak to select')
parsearg.add_argument('--peakwl', type=float, default=6562.8, help='Central wavelength of peak')
parsearg.add_argument('--peakwidth', type=float, default=2.0, help='Width of peak in Angstroms')
parsearg.add_argument('--xwidth', type=float, default=20.0, help='Width of X range around peak in Angstroms')

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

# Get wavelength for peak and possibly doppler-ise it.

peakwl = res['peakwl']
simb = res['simbadrv']
if simb is not None:
    rv = simbad.getrv(simb)
    if rv != 0.0:
        npeakwl = doppler.rev_doppler(peakwl, rv)
        print "%s: Adjusting wavelength from %.2f to %.2f for rv of %#.2g" % (simb, peakwl, npeakwl, rv)
        peakwl = npeakwl

rlist = datarange.init_default_ranges(peakshort = res['peakname'],
                                      peakdescr = res['peakdescr'],
                                      peakwl = peakwl,
                                      peakwid = res['peakwidth'],
                                      xwid = res['xwidth'])
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
