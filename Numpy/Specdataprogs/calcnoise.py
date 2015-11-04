#! /usr/bin/env python

import sys
import os
import os.path
import string
import argparse
import numpy as np
import miscutils
import specdatactrl
import specinfo
import noise

parsearg = argparse.ArgumentParser(description='Batch mode calculate noise for set of spectra')
parsearg.add_argument('infofile', type=str, help='Specinfo file', nargs=1)
parsearg.add_argument('--first', type=int, default=0, help='First spectrum number to use')
parsearg.add_argument('--last', type=int, default=10000000, help='Last spectrum number to use')
parsearg.add_argument('--precison', type=int, default=2, help='Deccimal places precision')

res = vars(parsearg.parse_args())

infofile = res['infofile'][0]
firstspec = res['first']
lastspec = res['last']
prec = res['precison']

fmt = "%%.%df" % prec

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

try:
    ctrllist.loadfiles()
except specdatactrl.SpecDataError as e:
    sys.stdout = sys.stderr
    print "Problem loading files via", infofile
    print "Error was:", e.args[0]
    sys.exit(101)

# Process data according to day

resultsy = np.array([], dtype=np.float64)
resultse = np.array([], dtype=np.float64)

for n, spectrum in enumerate(ctrllist.datalist):
    
    if n < firstspec or n > lastspec:
        continue

    # Get spectral data but skip over ones we've already marked to ignore
    try:
        yvals = spectrum.get_yvalues(False)
        yerrs = spectrum.get_yerrors(False)
    except specdatactrl.SpecDataError:
        continue

    resultsy = np.concatenate((resultsy, yvals))
    resultse = np.concatenate((resultse, yerrs))

print fmt % noise.getnoise(resultsy, resultse)
sys.exit(0)
