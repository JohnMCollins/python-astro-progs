#! /usr/bin/env python

import argparse
import scipy.signal as ss
import numpy as np
import string
import sys
import os
import rangearg
import fakeobs

parsearg = argparse.ArgumentParser(description='Compute ew and subpeak profiles')
parsearg.add_argument('spec', type=str, help='Spectrum files', nargs='+')
parsearg.add_argument('--obstimes', type=str, help='File for observation times')
parsearg.add_argument('--xcolumn', help='Column in data for X values', type=int, default=0)
parsearg.add_argument('--ycolumn', help='Column in data for Y values', type=int, default=1)
parsearg.add_argument('--central', type=float, default=6563.0, help='Central wavelength value def=6563')
parsearg.add_argument('--ithresh', type=float, default=10.0, help='Percent threshold for EW selection')
parsearg.add_argument('--continuum', type=float, default=1.0, help='Continuum value')
parsearg.add_argument('--outew', type=str, help='Output equivalent width file')
parsearg.add_argument('--outpr', type=str, help='Output peak ratio file')

resargs = vars(parsearg.parse_args())

spec = resargs['spec']
xcolumn = resargs['xcolumn']
ycolumn = resargs['ycolumn']

central = resargs['central']
ithreshold = resargs['ithresh']
con = resargs['continuum']
threshv = con + ithreshold / 100.0

outew = resargs['outew']
outpr = resargs['outpr']

if outew is None:
    print "No ew file out given"
    sys.exit(5)
if outpr is None:
    print "No pr file out given"
    sys.exit(6)

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
  
    maxinten = -1e6
    maxintenplace = -1

    for mn in minima:
        maxintenplace = mn
        maxinten = amps[mn]

    sel = amps > threshv
    ewpl = np.where(sel)[0]
    ewplf = ewpl[0]
    ewpll = ewpl[-1]
    ewlow = wavelengths[ewplf]
    ewhi = wavelengths[ewpll]
    ew = np.trapz(amps[ewplf:ewpll]-1.0, wavelengths[ewplf:ewpll]) / (ewhi - ewlow)
    if maxinten > -1e6:
        sel = amps >= maxinten
        mipl = np.where(sel)[0]
        miplf = mipl[0]
        mipll = mipl[-1]
        lhorn = np.trapz(amps[miplf:maxintenplace]-maxinten, wavelengths[miplf:maxintenplace]) / (wavelengths[maxintenplace]-wavelengths[miplf])
        rhorn = np.trapz(amps[maxintenplace:mipll]-maxinten, wavelengths[maxintenplace:mipll]) / (wavelengths[mipll]-wavelengths[maxintenplace])
        hr = rhorn / lhorn
    else:
        hr = 1.0
    
    results.append([obst, ew, hr])

resulta = np.array(results)
resulta = resulta.transpose()
ewres = np.array([resulta[0], resulta[1]])
hrres = np.array([resulta[0], resulta[2]])
ewres = ewres.transpose()
hrres = hrres.transpose()

np.savetxt(outew, ewres)
np.savetxt(outpr, hrres)