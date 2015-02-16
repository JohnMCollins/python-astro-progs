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
parsearg.add_argument('--ithresh', type=float, default=10.0, help='Percent threshold for EW selection')
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
ithresh = res['ithresh']
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
    
    if len(sigmins) == 0:
        
    
    for mx in sigmaxes:
        plt.axvline(scaledwl[mx], color='brown')
    for mn in sigmins:
        plt.axvline(scaledwl[mn], color='purple')
    plt.legend()

plt.show()
sys.exit(0)
