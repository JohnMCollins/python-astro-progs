#! /usr/bin/env python

# Integrate the H alpha peaks to get figures for the total values,
# assume continuum is normalised at 1 unless otherwise specified

import argparse
import os.path
import sys
import numpy as np
import specdatactrl
import datarange
import xmlutil
import meanval
import exclusions

parsearg = argparse.ArgumentParser(description='Get sizes of H Alpha peaks')
parsearg.add_argument('--rangefile', type=str, help='Range file')
parsearg.add_argument('--specfile', type=str, help='Spectrum data controlfile')
parsearg.add_argument('--outfile', type=str, help='Output file')
parsearg.add_argument('--continuum', type=float, default=1.0, help='Value for continuum')
parsearg.add_argument('--excludes', type=str, help='File for output of excluded data')

SPC_DOC_ROOT = "spcctrl"
SPC_DOC_NAME = "SPCCTRL"

res = vars(parsearg.parse_args())
rf = res['rangefile']
sf = res['specfile']
outf = res['outfile']
exclf = res['excludes']
continuum = res['continuum']

if rf is None:
    print "No range file specified"
    sys.exit(100)

if sf is None:
    print "No spec data control specified"
    sys.exit(101)

if outf is None:
    print "No output file specified"
    sys.exit(102)

try:
    doc, root = xmlutil.load_file(sf, SPC_DOC_ROOT)
    spclist = specdatactrl.SpecDataList(sf)
    cnode = xmlutil.find_child(root, "cfile")
    spclist.load(cnode)
except xmlutil.XMLError as e:
    print "Load control file XML error", e.args[0]
    sys.exit(50)

try:
    rangelist = datarange.load_ranges(rf)
except datarange.DataRangeError as e:
    print "Range load error", e.args[0]
    sys.exit(51)

try:
    halphar = rangelist.getrange("halpha")
except datarange.DataRangeError as e:
    print e.args[0]
    sys.exit(52)

print "Loading data files"

try:
    spclist.loadfiles()
except specdatactrl.SpecDataError as e:
    print "Loading spectral data error", e.args[0]
    sys.exit(53)

print "load complete"

skipped = 0
elist = exclusions.Exclusions()
datelu = dict()

for dataset in spclist.datalist:
    try:
        xvalues = dataset.get_xvalues(False)
        yvalues = dataset.get_yvalues(False)
    except specdatactrl.SpecDataError as err:
        if err.args[0] == "Discounted data":
            elist.add(dataset.modbjdate, err.args[2])
        skipped += 1
        continue
    har, hir = meanval.mean_value(halphar, xvalues, yvalues)
    ew = (hir - continuum * har) / har
    datelu[dataset.modbjdate] = ew

print "Integration complete, skipped", skipped, "data files"
if skipped > 0 and exclf is not None:
    try:
        elist.save(exclf)
    except ExcludeError as e:
        print e.args[0], e.args[1]
        sys.exit(54)

ds = datelu.keys()
ds.sort()
dates = []
ews = []
for d in ds:
    dates.append(d)
    ews.append(datelu[d])

nparr = np.array([dates, ews]).transpose()
np.savetxt(outf, nparr)


