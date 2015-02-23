#! /usr/bin/env python

import argparse
import scipy.signal as ss
import scipy.integrate as si
import numpy as np
import string
import sys
import os
import glob
import rangearg
import fakeobs
import findprofile

parsearg = argparse.ArgumentParser(description='Compute ew and subpeak profiles')
parsearg.add_argument('spec', type=str, help='Spectrum files', nargs='+')
parsearg.add_argument('--glob', action='store_true', help='Apply glob to arguments')
parsearg.add_argument('--obstimes', type=str, help='File for observation times')
parsearg.add_argument('--xcolumn', help='Column in data for X values', type=int, default=0)
parsearg.add_argument('--ycolumn', help='Column in data for Y values', type=int, default=1)
parsearg.add_argument('--central', type=float, default=6563.0, help='Central wavelength value def=6563')
parsearg.add_argument('--degfit', type=int, default=10, help='Degree of fitting polynomial')
parsearg.add_argument('--ithresh', type=float, default=2.0, help='Percent threshold for EW selection')
parsearg.add_argument('--sthresh', type=float, default=50.0, help='Percent threshold for considering maxima and minima')
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
degfit = resargs['degfit']
ithresh = resargs['ithresh'] / 100.0 
sthresh = resargs['sthresh'] / 100.0

outew = resargs['outfile']

if outew is None:
    print "No ew file out given"
    sys.exit(5)

obstimes = dict()
obstimefile = resargs['obstimes']    
if obstimefile is None:
    print "No obs times file given"
    sys.exit(208)
obstimes = fakeobs.getfakeobs(obstimefile)
if obstimes is None:
    print "Cannot read fake obs file", obstimefile
    sys.exit(209)
if xcolumn == ycolumn:
    print "Cannot have X and Y columns the same"
    sys.exit(210)

results = []
errors = 0
nohorns = 0

for sf in spec:
    try:
        arr = np.loadtxt(sf, unpack=True)
        wavelengths = arr[xcolumn]
        amps = arr[ycolumn]
    except IOError as e:
        print "Could not load spectrum file", sf, "error was", e.args[1]
        sys.exit(211)
    except ValueError:
        print "Conversion error on", sf
        sys.exit(212)
    except IndexError:
        print "Do not believe columns x column", xcolumn, "y column", ycolumn
        sys.exit(213)
            
    obst = obstimes[sf]
    prof = findprofile.Specprofile(degfit = degfit)
    
    try:
        
        prof.calcprofile(wavelengths, amps, central = central, sigthreash = sthresh, intthresh = ithresh)
    
    except findprofile.FindProfileError as e:
    
        errors += 1
        nohorns += 1
        print "Error -", e.args[0], "in file", sf
        ew = hs = 0.0
        hr = 1.0
        results.append([obst, ew, hs, hr])
        continue
    
    ewleft, ewright = prof.ewinds
    ewsz = si.simps(amps[ewleft:ewright+1]-1.0, wavelengths[ewleft:ewright+1])
    ew = ewsz / (wavelengths[ewright] - wavelengths[ewleft])
    
    if prof.twinpeaks:
                
        lhmax, rhmax = prof.maxima
        minind = prof.minima[0]
        minamp = amps[minind]
        below_minamp = np.where(amps < minamp)[0]
        lwhere = below_minamp[below_minamp < lhmax][-1] + 1
        rwhere = below_minamp[below_minamp > rhmax][0] - 1
        lhornsz = si.simps(amps[lwhere:minind+1] - 1.0, wavelengths[lwhere:minind+1])
        rhornsz = si.simps(amps[minind:rwhere+1]- 1.0, wavelengths[minind:rwhere+1])
        lhorn = lhornsz / (wavelengths[minind] - wavelengths[lwhere])
        rhorn = rhornsz / (wavelengths[rwhere] - wavelengths[minind])

        hr = rhorn / lhorn
        hs = (lhornsz + rhornsz) / ewsz
        
    else:
        hr = 1.0
        hs = 0.0
        nohorns += 1
    
    results.append([obst, ew, hs, hr])

results = np.array(results)

np.savetxt(outew, results)
ecode = 0
lr = len(results)
if errors > 0:
    ecode = 1
    if errors == lr:
        ecode += 4
        print "Could not find EW in all cases"
    else:
        print "Could not find EW in %d out of %d cases" % (errors, lr)
if nohorns > 0:
    ecode += 2
    if nohorns == lr:
        ecode += 8
        print "Could not find peaks in all cases"
    else:
        print "Could not find peaks in %d out of %d cases" % (nohorns, lr) 
sys.exit(ecode)
