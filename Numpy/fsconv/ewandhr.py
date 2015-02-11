#! /usr/bin/env python

import argparse
import scipy.signal as ss
import numpy as np
import string
import sys
import os
import glob
import rangearg
import fakeobs

parsearg = argparse.ArgumentParser(description='Compute ew and subpeak profiles')
parsearg.add_argument('spec', type=str, help='Spectrum files', nargs='+')
parsearg.add_argument('--glob', action='store_true', help='Apply glob to arguments')
parsearg.add_argument('--obstimes', type=str, help='File for observation times')
parsearg.add_argument('--xcolumn', help='Column in data for X values', type=int, default=0)
parsearg.add_argument('--ycolumn', help='Column in data for Y values', type=int, default=1)
parsearg.add_argument('--central', type=float, default=6563.0, help='Central wavelength value def=6563')
parsearg.add_argument('--ithresh', type=float, default=10.0, help='Percent threshold for EW selection')
parsearg.add_argument('--continuum', type=float, default=1.0, help='Continuum value')
parsearg.add_argument('--outfile', type=str, help='Output file')

resargs = vars(parsearg.parse_args())

spec = resargs['spec']

if resargs['glob']:
    sfs = spec
    spec = []
    for sf in sfs:
        gs = glob.glob(sf)
        gs.sort()
        spec.extend(gs)

xcolumn = resargs['xcolumn']
ycolumn = resargs['ycolumn']

central = resargs['central']
ithreshold = resargs['ithresh']
con = resargs['continuum']
threshv = con + ithreshold / 100.0

outew = resargs['outfile']

if outew is None:
    print "No ew file out given"
    sys.exit(5)

obstimes = dict()
obstimefile = resargs['obstimes']    
if obstimefile is None:
    print "No obs times file given"
    sys.exit(8)
obstimes = fakeobs.getfakeobs(obstimefile)
if obstimes is None:
    print "Cannot read fake obs file", obstimefile
    sys.exit(9)
if xcolumn == ycolumn:
    print "Cannot have X and Y columns the same"
    sys.exit(10)

results = []

for sf in spec:
    try:
        arr = np.loadtxt(sf, unpack=True)
        wavelengths = arr[xcolumn]
        amps = arr[ycolumn]
    except IOError as e:
        print "Could not load spectrum file", sf, "error was", e.args[1]
        sys.exit(11)
    except ValueError:
        print "Conversion error on", sf
        sys.exit(12)
    except IndexError:
        print "Do not believe columns x column", xcolumn, "y column", ycolumn
        sys.exit(13)
        
    obst = obstimes[sf]

    maxima = ss.argrelmax(amps)[0]
    minima = ss.argrelmin(amps)[0]

    if len(maxima) == 0 or len(maxima) > 2:

        # No peak or lots of peaks, we're not clever enough right now

        ew = hs = 0.0
        hr = 1.0

    elif len(maxima) == 1:

        # Just one maximum no horns

        hs = 0.0
        hr = 1.0

        sel = amps > threshv
        ewpl = np.where(sel)[0]
        if len(ewpl) < 2:
            ew = 0.0
        else:
            ewplf = ewpl[0]
            ewpll = ewpl[-1]
            ew =  np.trapz(amps[ewplf:ewpll+1]-1.0, wavelengths[ewplf:ewpll+1]) / (wavelengths[ewpll] - wavelengths[ewplf])

    else:

        # Two maxmima with min in between.

        minplace = minima[0]
        mininten = amps[minplace]

        # Do equivalent width as before

        sel = amps > threshv
        ewpl = np.where(sel)[0]

        if len(ewpl) < 2:
            ew = hs = 0.0
            hr = 1.0
        else:
            ewplf = ewpl[0]
            ewpll = ewpl[-1]
            ewlow = wavelengths[ewplf]
            ewhi = wavelengths[ewpll]
            ewsz = np.trapz(amps[ewplf:ewpll+1]-1.0, wavelengths[ewplf:ewpll+1])
            ew =  ewsz / (ewhi - ewlow)

            # Extract the left and right horns

            sel = amps >= mininten
            mipl = np.where(sel)[0]

            if len(mipl) < 2 or abs(ewsz) < 1e-6:

                # Too minimal forget it

                hr = 1.0
                hs = 0.0

            else:
                miplf = mipl[0]
                mipll = mipl[-1]

                lhornsz = np.trapz(amps[miplf:minplace+1] - mininten, wavelengths[miplf:minplace+1])
                rhornsz = np.trapz(amps[minplace:mipll+1]- mininten, wavelengths[minplace:mipll+1])
                lhorn = lhornsz / (wavelengths[minplace] - wavelengths[miplf])
                rhorn =  rhornsz / (wavelengths[mipll] - wavelengths[minplace])

                hr = rhorn / lhorn
                hs = (lhornsz + rhornsz) / ewsz

    results.append([obst, ew, hs, hr])

results = np.array(results)

np.savetxt(outew, results)
