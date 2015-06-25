#! /usr/bin/env python

# Display spec data handling in info file

import argparse
import os.path
import sys
import string
import datarange
import specinfo
import miscutils
import jdate
import specdatactrl

def printoffscale(thing):
    """Display values of offset and scale"""
    ind = isinstance(thing, specdatactrl.SpecDataArray)
    if thing.xscale != 1.0:
        if ind: print "\t",
        print "X Scale: %#.15g" % thing.xscale
    if thing.yscale != 1.0:
        if ind: print "\t",
        print "Y Scale: %#.15g" % thing.yscale
    if thing.xoffset != 0.0:
        if ind: print "\t",
        print "X Offset: %#.15g" % thing.xoffset
    if thing.yoffset is not None:
        if ind: print "\t",
        print "Y offset:", string.join(["%#.6g" % rp for rp in thing.yoffset], ' ')

parsearg = argparse.ArgumentParser(description='List info on spectra in spectral data file')
parsearg.add_argument('infofile', help="XML file of spec info", nargs='+', type=str)
parsearg.add_argument('--outfile', help="Output file if not STDOUT", type=str)
parsearg.add_argument('--latex', help='Latex output format', action='store_true')
parsearg.add_argument('--full', help='Display full details with continuum polys etc', action='store_true')

res = vars(parsearg.parse_args())
rfs = res['infofile']
outf = res['outfile']
latex = res['latex']
fulldets = res['full']

save_stdout = sys.stdout
ofil = sys.stdout

if outf is not None:
    try:
        ofil = open(outf, 'w')
    except IOError as e:
        sys.stdout = sys.stderr
        print "Error creating output file", outf, "error was", e.args[1]
        sys.exit(100)

errors = 0
had = 0
sys.stdout = ofil

for rf in rfs:
    if not os.path.isfile(rf):
        rf = miscutils.replacesuffix(rf, specinfo.SUFFIX)
    try:
        sinf = specinfo.SpecInfo()
        sinf.loadfile(rf)
        clist = sinf.get_ctrlfile()
    except specinfo.SpecInfoError as e:
        sys.stdout = sys.stderr
        print "Control load error on file", rf
        print "Error was:"
        print e.args[0]
        errors += 1
        sys.stdout = ofil
        continue
    if fulldets:
        printoffscale(clist)

    for spn, spectrum in enumerate(clist.datalist):
        dat = spectrum.modjdate
        if dat == 0: dat = spectrum.modbjdate
        dt = jdate.jdate_to_datetime(dat)
        print "%.3d:" % (spn+1.), dt.strftime("%d %b %Y %H:%M:%S:"),
        if spectrum.remarks is not None:
            if spectrum.discount: print "(",
            print spectrum.remarks,
            if spectrum.discount: print ")",
        print
        if fulldets:
            printoffscale(spectrum)
