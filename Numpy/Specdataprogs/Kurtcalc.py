#! /usr/bin/env python

import sys
import os
import os.path
import string
import warnings
import argparse
import math
import numpy as np
import scipy.stats as ss
import miscutils
import specdatactrl
import datarange
import specinfo

warnings.simplefilter('error')

parsearg = argparse.ArgumentParser(description='Batch mode calculate Skew/Kurtosis', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('infofile', type=str, help='Specinfo file', nargs=1)
parsearg.add_argument('--rangename', type=str, default='halpha', help='Range name to calculate from')
parsearg.add_argument('--outfile', help='Output file name', type=str, required=True)
parsearg.add_argument('--first', type=int, default=0, help='First spectrum number to use')
parsearg.add_argument('--last', type=int, default=10000000, help='Last spectrum number to use')
parsearg.add_argument('--divspec', type=int, nargs='+', help='Divide given spectrum number(s) into display')

res = vars(parsearg.parse_args())

infofile = res['infofile'][0]
rangename = res['rangename']
outfile = res['outfile']
firstspec = res['first']
lastspec = res['last']
divspec = res['divspec']

if not os.path.isfile(infofile):
    infofile = miscutils.replacesuffix(infofile, specinfo.SUFFIX)

try:
    inf = specinfo.SpecInfo()
    inf.loadfile(infofile)
    ctrllist = inf.get_ctrlfile()
    rangl = inf.get_rangelist()
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

try:
    selected_range = rangl.getrange(rangename)
except datarange.DataRangeError as e:
    print "Cannot select range", rangename, "error was", e.args[0]
    sys.exit(13)

ifuncs = []

if divspec is not None:
    for exs in divspec:
        try:
            ef = ctrllist.datalist[exs]
            exx = ef.get_xvalues()
            exy = ef.get_yvalues()
        except IndexError:
            sys.stdout = sys.stderr
            print "Invalid div spectrum", exs
            sys.exit(12)
        except specinfo.SpecInfoError:
            print "Invalid spectrum number", exs
            sys.exit(12)
        ifuncs.append(sint.interp1d(exx, exy, fill_value=exy[0], bounds_error=False))

# Process data according to day

results = []

for n, spectrum in enumerate(ctrllist.datalist):
    
    if n < firstspec or n > lastspec:
        continue

    # Get spectral data but skip over ones we've already marked to ignore
    try:
        xvalues = spectrum.get_xvalues(False)
        yvalues = spectrum.get_yvalues(False)
    except specdatactrl.SpecDataError:
        continue
   
    if len(ifuncs) != 0:
        xvl = len(xvalues)
        adjamps = np.array([]).reshape(0, xvl)
        for ifn in ifuncs:
            adjamps = np.concatenate((adjamps, ifn(xvalues).reshape(1, xvl)))
        adjamps = adjamps.mean(axis=0) 
        yvalues /= adjamps

    rx, ry = selected_range.select(xvalues, yvalues)
    sk = ss.skew(ry)
    kt = ss.kurtosis(ry)
    results.append((spectrum.modjdate, spectrum.modbjdate, sk, 0.0, kt, 0.0, 1.0, 0.0))

np.savetxt(outfile, results)

sys.exit(0)
