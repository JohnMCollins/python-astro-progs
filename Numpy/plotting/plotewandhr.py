#! /usr/bin/env python

# Find the shape of spectra and get EW

import argparse
import os.path
import sys
import string
import numpy as np
import matplotlib.pyplot as plt
import scipy.signal as ss
import rangearg

parsearg = argparse.ArgumentParser(description='Find maxima etc of plot to get equivalent width')
parsearg.add_argument('specs', type=str, nargs='+', help='Spectrum files')
parsearg.add_argument('--xrange', type=str, help='Range for X axis')
parsearg.add_argument('--central', type=float, default=6563.0, help='Central wavelength value def=6563')
parsearg.add_argument('--degfit', type=int, default=10, help='Degree of fitting polynomial')
parsearg.add_argument('--ithresh', type=float, default=2.0, help='Percent threshold for EW selection')
parsearg.add_argument('--sthresh', type=float, default=50.0, help='Percent threshold for considering maxima and minima')
parsearg.add_argument('--ylab', type=str, help='Label for plot Y axis', default='Intensity')
parsearg.add_argument('--xlab', type=str, default='Wavelength (offset from central)', help='Label for plot X axis')
parsearg.add_argument('--width', type=float, default=8, help='Display width')
parsearg.add_argument('--height', type=float, default=6, help='Display height')

res = vars(parsearg.parse_args())
specfiles = res['specs']
xrange = rangearg.parserange(res['xrange'])
central = res['central']
degfit = res['degfit']
dims = (res['width'], res['height'])
xlab = res['xlab']
ylab = res['ylab']
ithresh = 1.0 + res['ithresh'] / 100.0 
sthresh = res['sthresh']

for sf in specfiles:
    try:
        arr = np.loadtxt(sf, unpack=True)
        wavelengths = arr[0]
        amps = arr[1]
    except IOError as e:
        print "Could not load spectrum file", sf, "error was", e.args[1]
        sys.exit(211)
    except ValueError:
        print "Conversion error on", sf
        sys.exit(212)
    
    plt.figure(figsize=dims)
    if xrange is not None:
        plt.xlim(*xrange)
    plt.xlabel(xlab)
    plt.ylabel(ylab)
    
    scaledwl = wavelengths - central
    plt.plot(scaledwl, amps, label='spectrum', color='blue')
      
    minamp = np.min(amps)
    maxamp = np.max(amps)
    diffamp = (maxamp-minamp)*sthresh / 100.0
         
    specmax = ss.argrelmax(amps)[0]
    specmin = ss.argrelmin(amps)[0]  
    sigmins = specmin[(amps[specmin] - minamp) >= diffamp]
    sigmaxes = specmax[(amps[specmax] - minamp) >= diffamp]
    
    bthresh = np.argwhere(amps < ithresh).flatten()
    
    singlemaxind = lmaxind = rmaxind = minind = -1   
        
    if len(sigmins) == 0:
        if len(sigmaxes) == 0:
            print "Could not figure shape in", sf, "No maxes or mmins"
            continue
        if len(sigmaxes) > 2:
            print "Could not figure shape in", sf, "No mins", len(sigmaxes), "maxes"
            continue
        if len(sigmaxes) == 1:
            lmaxind = rmaxind = singlemaxind = sigmaxes[0]
        else:
            # Case where we have 2 maxima but we didn't find the minimum
            # First try without limiting minimum
            
            lmaxind, rmaxind = sigmaxes
            restrwl = scaledwl[lmaxind:rmaxind+1]
            restramp = amps[lmaxind:rmaxind+1]
            limmins = ss.argrelmin(restramp)[0]
            if len(limmins) == 1:
                # That did it
                minind = limmins[0] + lmaxind
                print "First pass did it", minind
            else:
                # Fit a polynomial to section between 2 maxima and get minimum
                # from that
                coeffs = np.polyfit(restrwl, restramp, degfit)
                pvals = np.polyval(coeffs, restrwl)
                pminima = ss.argrelmin(pvals)[0]
                if len(pminima) == 0:
                    # Try roots later if we get this
                    print "Still could not find minimum between two maxima in", sf
                    continue
                minmins = np.argsort(np.polyval(coeffs, restrwl[pminima]))
                minind = pminima[minmins[0]] + lmaxind
                print "Second pass did it", minind
    
    elif len(sigmins) == 1:
        
        minind = sigmins[0]
        
        if len(sigmaxes) != 2:
            print "Could not figure shape in", sf, "nmaxes =", len(sigmaxes)
            for mx in sigmaxes: plt.axvline(scaledwl[mx], color='brown')
            plt.axvline(scaledwl[minind], color='green')
            continue
        
        lmaxind, rmaxind = sigmaxes
                
        if not (lmaxind < minind < rmaxind):
            print "Could not understand shape in", sf, "with lmaxind =", lmaxind, "rmaxind =", rmaxind, "minind =", minind
            for mx in sigmaxes: plt.axvline(scaledwl[mx], color='brown')
            plt.axvline(scaledwl[minind], color='green')
            continue
        
    leftinds = bthresh[bthresh < lmaxind]
    rightinds = bthresh[bthresh > rmaxind]
        
    try:           
        leftew = leftinds[-1]+1
    except IndexError:
        leftew = 0
    try:
        rightew = rightinds[0]-1
    except IndexError:
        rightew = len(amps)-1
    
    if minind >= 0:
        plt.axvline(scaledwl[minind], color='green', label='central')
    if singlemaxind >= 0:
        plt.axvline(scaledwl[singlemaxind], color='red', label='Maximum')
    else:
        plt.axvline(scaledwl[lmaxind], color='red', label='blue horn')
        plt.axvline(scaledwl[rmaxind], color='red', label='red horn')
    plt.axvline(scaledwl[leftew], color='purple', label='ew')
    plt.axvline(scaledwl[rightew], color='purple', label='ew')
    plt.legend()

plt.show()
sys.exit(0)
