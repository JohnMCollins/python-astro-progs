#! /usr/bin/env python

import sys
import os
import os.path
import string
import locale
import argparse
import numpy as np
import scipy.interpolate as sint
import miscutils
import specdatactrl
import datarange
import specinfo
import equivwidth
import meanval
import noise

parsearg = argparse.ArgumentParser(description='Batch mode calculate continue')
parsearg.add_argument('infofile', type=str, help='Specinfo file', nargs=1)
parsearg.add_argument('--rangename', type=str, default='halpha', help='Range name to calculate equivalent widths')
parsearg.add_argument('--peakranges', type=str, default='integ1,integ2', help='Range names for subpeaks')
parsearg.add_argument('--outfile', help='Output file name', type=str, required=True)
parsearg.add_argument('--snr', type=float, default=-1e6, help='Omit points with SNR worse than given')
parsearg.add_argument('--first', type=int, default=0, help='First spectrum number to use')
parsearg.add_argument('--last', type=int, default=10000000, help='Last spectrum number to use')
parsearg.add_argument('--subspec', type=int, help='Subtract given spectrum number from display')
parsearg.add_argument('--divspec', type=int, help='Divide given spectrum number from display')

res = vars(parsearg.parse_args())

infofile = res['infofile'][0]
rangename = res['rangename']
peakranges = string.split(res['peakranges'], ',')
if len(peakranges) != 2:
    print "Expecting 2 peak ranges"
    sys.exit(9)
outfile = res['outfile']

snr = res['snr']

firstspec = res['first']
lastspec = res['last']
subspec = res['subspec']
divspec = res['divspec']

if subspec is not None and divspec is not None:
    print "Cannot have beth subspec and divspec"
    sys.exit(31)

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

# If we haven't got subpeak stuff just set to none.

try:
    integ1 = rangl.getrange(peakranges[0])
    integ2 = rangl.getrange(peakranges[1])
except datarange.DataRangeError:
    integ1 = integ2 = None

exspec = subspec
if exspec is None: exspec = divspec
ifunc = None

if exspec is not None:
    try:
        ef = cfile.datalist[exspec]
        exx = ef.get_xvalues()
        exy = ef.get_yvalues()
    except IndexError:
        sys.stdout = sys.stderr
        print "Invalid sub/div spectrum"
        sys.exit(12)
    except specinfo.SpecInfoError:
        print "Invalid spectrum number", exspec
        sys.exit(12)
    ifunc=sint.interp1d(exx, exy, fill_value=exy[0], bounds_error=False)
    
# Process data according to day

results = []

for n, spectrum in enumerate(ctrllist.datalist):
    
    if n < firstspec or n > lastspec:
        continue

    # Get spectral data but skip over ones we've already marked to ignore
    try:
        xvalues = spectrum.get_xvalues(False)
        yvalues = spectrum.get_yvalues(False)
        yerrs = spectrum.get_yerrors(False)
    except specdatactrl.SpecDataError:
        continue

    if snr > -1000.0 and noise.getnoise(yvalues, yerrs) < snr: continue
    
    if ifunc is not None:
        adjamps = ifunc(xvalues)
        if divspec is None:
            yvalues -= adjamps
        else:
            yvalues /= adjamps

    ew = equivwidth.equivalent_width(selected_range, xvalues, yvalues)

    ps = pr = 1.0
    if integ1 is not None:
        peak1w, peak1s = meanval.mean_value(integ1, xvalues, yvalues)
        peak2w, peak2s = meanval.mean_value(integ2, xvalues, yvalues)
        ps = (peak2s * peak1w) / (peak1s * peak2w)
        pr = equivwidth.equivalent_width(integ2, xvalues, yvalues) / equivwidth.equivalent_width(integ1, xvalues, yvalues)

    #lastdate = spectrum.modjdate
    #if lastdate == 0: lastdate = spectrum.modbjdate

    results.append((spectrum.modjdate, spectrum.modbjdate, ew, 0.0, ps, 0.0, pr, 0.0))

np.savetxt(outfile, results)

sys.exit(0)
