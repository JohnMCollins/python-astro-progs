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
import findprofile

parsearg = argparse.ArgumentParser(description='Find maxima etc of plot to get equivalent width')
parsearg.add_argument('specs', type=str, nargs='+', help='Spectrum files')
parsearg.add_argument('--xrange', type=str, help='Range for X axis')
parsearg.add_argument('--central', type=float, default=6563.0, help='Central wavelength value def=6563')
parsearg.add_argument('--degfit', type=int, default=10, help='Degree of fitting polynomial')
parsearg.add_argument('--ithresh', type=float, default=2.0, help='Percent threshold for EW selection')
parsearg.add_argument('--sthresh', type=float, default=50.0, help='Percent threshold for considering maxima and minima')
parsearg.add_argument('--ignedge', type=float, default=5.0, help='Percentage of edges we ignore')
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
ithresh = res['ithresh'] / 100.0
sthresh = res['sthresh'] / 100.0
ign = res['ignedge']

errors = 0

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
    ax = plt.gca()
    ax.get_xaxis().get_major_formatter().set_useOffset(False)
    plt.plot(wavelengths, amps, label='spectrum', color='blue')

    prof = findprofile.Specprofile(degfit = degfit, ignoreedge=ign)
    try:
        prof.calcprofile(wavelengths, amps, central = central, sigthresh = sthresh, intthresh = ithresh)
    except findprofile.FindProfileError as e:
        errors += 1
        print "Error -", e.args[0], "in file", sf
    if prof.maxima is not None:
        for mx in prof.maxima: plt.axvline(wavelengths[mx], color='red', label='Maximum')
    if prof.minima is not None:
        for mn in prof.minima: plt.axvline(wavelengths[mn], color='green', label='Minimum')
    if prof.ewinds is not None:
        for ew in prof.ewinds: plt.axvline(wavelengths[ew], color='purple', label='ew')
    plt.legend()
plt.show()
if errors > 0:
    sys.exit(1)
sys.exit(0)
