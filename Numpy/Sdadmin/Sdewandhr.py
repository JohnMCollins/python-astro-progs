#! /usr/bin/env python

import sys
import os
import os.path
import locale
import argparse
import numpy as np
import xml.etree.ElementTree as ET
import xmlutil
import datarange
import specdatactrl
import miscutils
import meanval
import exclusions

SPC_DOC_NAME = "SPCCTRL"
SPC_DOC_ROOT = "spcctrl"

parsearg = argparse.ArgumentParser(description='Get table of EWs from spectral data files')
parsearg.add_argument('--rangefile', type=str, help='Range file')
parsearg.add_argument('--specfile', type=str, help='Spectrum data control file')
parsearg.add_argument('--ewrange', type=str, default='halpha', help='Range to select for calculating EW')
parsearg.add_argument('--bluehorn', type=str, help='Range 1 for calculating sub-peaks')
parsearg.add_argument('--redhorn', type=str, help='Range 2 for calculating sub-peaks')
parsearg.add_argument('--outfile', type=str, help='Output file name')

resargs = vars(parsearg.parse_args())

rangefile = resargs['rangefile']
specfile = resargs['specfile']
ewrangename = resargs['ewrange']
bhrangename = resargs['bluehorn']
rhrangename = resargs['redhorn']
outfile = resargs['outfile']

if outfile is None:
    outf = sys.stdout
else:
    try:
        outf = open(outfile, 'w')
    except IOError as e:
        sys.stdout = sys.stderr
        print "Could not open", outfile, "error was", e.args[1]
        sys.exit(9)

if rangefile is not None:
    rangefile = miscutils.addsuffix(rangefile, '.spcr')
if specfile is not None:
    specfile = miscutils.addsuffix(specfile, '.sac')

if rangefile is None:
    if specfile is None:
        sys.stdout = sys.stderr
        print "No range file or spec ctrl file given"
        sys.exit(10)
    rangefile = miscutils.replacesuffix(specfile, 'spcr')
if specfile is None:
    specfile = miscutils.replacesuffix(rangefile, 'sac')

# Open control file

try:
    doc, root = xmlutil.load_file(specfile, SPC_DOC_ROOT)
    cf = specdatactrl.SpecDataList(specfile)
    cnode = xmlutil.find_child(root, "cfile")
    cf.load(cnode)
except xmlutil.XMLError as e:
    sys.stdout = sys.stderr
    print "Load control file XML error on", specfile
    print "error:", e.args[0]
    sys.exit(11)
except specdatactrl.SpecDataError as e:
    sys.stdout = sys.stderr
    print "Load control file data error", specfile
    print "error:", e.args[0]
    sys.exit(12)

# Open range file

try:
    rf = datarange.load_ranges(rangefile)
except datarange.DataRangeError as e:
    sys.stdout = sys.stderr
    print "Range load error", rangefile
    print "error:", e.args[0]
    sys.exit(13)

# Get range for EW IntegrationWarning

try:
    ewrange = rf.getrange(ewrangename)
except datarange.DataRangeError as e:
    sys.stdout = sys.stderr
    print "EW range error with", ewrangename, e.args[0]
    sys.exit(14)

bhrange = rhrange = None

if bhrangename is not None:
    if rhrangename is None:
        sys.stdout = sys.stderr
        print "Blue horn given but not red horn"
        sys.exit(15)
    elif bhrangename == rhrangename:
        sys.stdout = sys.stderr
        print "Red horn range is same as blue horn"
        sys.exit(16)
    try:
        bhrange = rf.getrange(bhrangename)
    except datarange.DataRangeError as e:
        sys.stdout = sys.stderr
        print "Blue horn range error with", bhrangename, e.args[0]
        sys.exit(17)
    try:
        rhrange = rf.getrange(rhrangename)
    except datarange.DataRangeError as e:
        sys.stdout = sys.stderr
        print "Red horn range error with", rhrangename, e.args[0]
        sys.exit(17)
elif rhrangename is not None:
    sys.stdout = sys.stderr
    print "Red horn given but not blue horn"
    sys.exit(15)

# Load up all the data

try:
    cf.loadfiles()
except specdatactrl.SpecDataError as e:
    sys.stdout = sys.stderr
    print "Error loading files", e.args[0]
    sys.exit(50)

if bhrange is None:
    results = np.empty(shape=(0,2), dtype=np.float64)
else:
    results = np.empty(shape=(0,5),dtype=np.float64)
skipped = 0

 # Compile list of equivalent widths for each spectrum
 # Note the ones we are excluding separately
        
for dataset in cf.datalist:
    try:
        xvalues = dataset.get_xvalues(False)
        yvalues = dataset.get_yvalues(False)
    except specdatactrl.SpecDataError as err:
        skipped += 1
        continue
    har, hir = meanval.mean_value(ewrange, xvalues, yvalues)
    ew = (hir - har) / har
    if bhrange is None:
        results = np.append(results,((dataset.modbjdate, ew),), axis=0)
    else:
        bhr, bir = meanval.mean_value(bhrange, xvalues, yvalues)
        rhr, rir = meanval.mean_value(rhrange, xvalues, yvalues)
        ps = (rir - rhr) / rhr + (bir - bhr) / bhr
        pr = (rir * bhr) / (bir * rhr)
        results = np.append(results, ((dataset.modbjdate, ew, ps, pr, np.log10(pr)),), axis=0)

np.savetxt(outf, results)

