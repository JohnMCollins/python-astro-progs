#! /usr/bin/env python

import sys
import os
import os.path
import re
import string
import locale
import argparse
import datetime

import numpy as np

import miscutils
import specdatactrl
import datarange
import specinfo


parsearg = argparse.ArgumentParser(description='Batch mode set jdates from file names')
parsearg.add_argument('infofiles', type=str, help='Specinfo file', nargs='+')
parsearg.add_argument('--force', action='store_true', help='Force change even if dates set')

res = vars(parsearg.parse_args())

infofiles = res['infofiles']
forceit = res['force']

errors = 0

for infofile in infofiles:
    
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
        errors += 1
        sys.stdout = sys.__stdout__
        continue
    
    if len(ctrllist.datalist) == 0:
        sys.stdout = sys.stderr
        print "No data files referred to in", infofile
        errors += 1
        sys.stdout = sys.__stdout__
        continue
    
    if ctrllist.datalist[0].modjdate != 0 and not forceit:
        sys.stdout = sys.stderr
        print "Already got dates in", infofile
        errors += 1
        sys.stdout = sys.__stdout__
        continue
    
    for spec in ctrllist.datalist:
        
        

try:
    ctrllist.loadfiles()
except specdatactrl.SpecDataError as e:
    sys.stdout = sys.stderr
    print "Problem loading files via", infofile
    print "Error was:", e.args[0]
    sys.exit(101)

inclrange = None
exclrange = None

try:
    if inclranges is not None and len(inclranges) != 0:
        inclrange = datarange.Rangeset(rangl)
        inclrange.parseset(inclranges)
except datarange.DataRangeError as e:
    sys.stdout = sys.stderr
    print "Problem seting include ranges"
    print "Error was:", e.args[0]
    sys.exit(102)
try:
    if exclranges is not None and len(exclranges) != 0:
        exclrange = datarange.Rangeset(rangl)
        exclrange.parseset(exclranges)
except datarange.DataRangeError as e:
    sys.stdout = sys.stderr
    print "Problem seting exclude ranges"
    print "Error was:", e.args[0]
    sys.exit(103)

# Remember how many we started with

pre_existing = ctrllist.count_markers()

# Do what we have to to reset markers etc

ndone = 0
if existact is not None and len(existact) != 0:
    existact = string.upper(existact[0:1])
    if  existact == 'R':
        ndone = ctrllist.reset_markers()
    elif existact == 'C':
        ndone = ctrllist.clear_remarks()

# So now we actually do the job

continua = []
dsfrom = []

for dataset in ctrllist.datalist:
    
    try:
        xvalues = dataset.get_xvalues(False)
        yvalues = dataset.get_yvalues(False)
    except specdatactrl.SpecDataError:
        continue
          
    lxv = len(xvalues)
        
    if lxv < 3:
        continue
    
    widths = np.concatenate(( (xvalues[1] - xvalues[0], ), (xvalues[2:] - xvalues[0:lxv-2]) / 2.0, (xvalues[-2] - xvalues[-1] ,)))
    
    if inclrange is not None:
        xvalues, yvalues, widths = inclrange.include(xvalues, yvalues, widths)
        if len(xvalues) < 3:
            continue
        
    if exclrange is not None:
        xvalues, yvalues, widths = exclrange.exclude(xvalues, yvalues, widths)

    continua.append(np.sum(yvalues * widths))
    dsfrom.append(dataset)
    
# Get median, mean and std deviation

cmedian = np.median(continua)
cmean = np.mean(continua)
cstd = np.std(continua)
selby = cmean
if medians: selby = cmedian
upperlim = selby + uppersd * cstd
lowerlim = selby - lowersd * cstd

nskipped = 0

for c, dataset in zip(continua, dsfrom):
    if lowerlim <= c <= upperlim: continue
    if c < lowerlim:
        dataset.skip('Below lower limit')
    else:
        dataset.skip('Above upper limit')
    nskipped += 1

if ndone == 0 and nskipped == 0:
    print "Nothing done, no changes"
    sys.exit(0)

try:
    inf.savefile()
except specinfo.SpecInfoError as e:
    sys.stdout = sys.stderr
    print "Cannot re-save", infofile
    print "Error was", e.args[0]
    sys.exit(150)

print "%d existing marks %d cleared %d newly set" % (pre_existing, ndone, nskipped)
sys.exit(0)