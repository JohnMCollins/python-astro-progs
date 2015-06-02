#! /usr/bin/env python

import argparse
import matplotlib.pyplot as plt
import scipy.signal as ss
import numpy as np
import string
import sys
import os
import rangearg


parsearg = argparse.ArgumentParser(description='Compute ew and subpeak profiles')
parsearg.add_argument('spec', type=str, help='Spectrum file', nargs=1)
parsearg.add_argument('--outfig', type=str, help='Output figure')
parsearg.add_argument('--title', help='Set window title', type=str, default="Spectrum display")
parsearg.add_argument('--xlab', type=str, help='Label for X axis', default='Wavelength ($\AA$)')
parsearg.add_argument('--ylab', type=str, help='Label for Y axis', default='Intensity')
parsearg.add_argument('--fork', action='store_true', help='Fork off daemon process to show plots and exit')
parsearg.add_argument('--width', help="Width of plot", type=float, default=8)
parsearg.add_argument('--height', help="Height of plot", type=float, default=6)
parsearg.add_argument('--xrange', help='Range of X values', type=str)
parsearg.add_argument('--yrange', help='Range of Y values', type=str)
parsearg.add_argument('--xpad', help='Padding round x', type=float, default=.25)
parsearg.add_argument('--ypad', help='Padding round y', type=float, default=.01)
parsearg.add_argument('--obstimes', type=str, help='File for observation times')
parsearg.add_argument('--xcolumn', help='Column in data for X values', type=int, default=0)
parsearg.add_argument('--ycolumn', help='Column in data for Y values', type=int, default=1)
parsearg.add_argument('--central', type=float, default=6563.0, help='Central wavelength value def=6563')
parsearg.add_argument('--ithresh', type=float, default=10.0, help='Percent threshold for EW selection')
parsearg.add_argument('--continuum', type=float, default=1.0, help='Continuum value')

resargs = vars(parsearg.parse_args())

spec = resargs['spec']
outfig = resargs['outfig']
xlab = resargs['xlab']
ylab = resargs['ylab']
forkoff = resargs['fork']
xcolumn = resargs['xcolumn']
ycolumn = resargs['ycolumn']
xrangelims = rangearg.parserange(resargs['xrange'])
yrangelims = rangearg.parserange(resargs['yrange'])
obstimes = dict()
obstimefile = resargs['obstimes']    
if obstimefile is not None:
    obstimes = fakeobs.getfakeobs(obstimefile)
    if obstimes is None:
        print "Cannot read fake obs file", obstimefile
        sys.exit(9)

if xcolumn == ycolumn:
    print "Cannot have X and Y columns the same"
    sys.exit(8)

plt.rcParams['figure.figsize'] = (resargs['width'], resargs['height'])
fig = plt.gcf()
fig.canvas.set_window_title(resargs['title'])
plt.gca().get_xaxis().get_major_formatter().set_useOffset(False)

try:
    arr = np.loadtxt(spec[0], unpack=True)
    wavelengths = arr[xcolumn]
    amps = arr[ycolumn]
except IOError as e:
    print "Could not load spectrum file", spec[0], "error was", e.args[1]
    sys.exit(11)
except ValueError:
    print "Conversion error on", spec[0]
    sys.exit(12)
except IndexError:
    print "Do not believe columns x column", xcolumn, "y column", ycolumn
    sys.exit(13)

yupper = np.max(amps)
ylower = np.min(amps)
xupper = np.max(wavelengths)
xlower = np.min(wavelengths)

if spec[0] in obstimes:
    legend = "%.4f" % obstimes[spec[0]]
else:
    legbits = string.split(spec[0], '.')
    legend = legbits[0]

pxlower = xlower - resargs['xpad']
pxupper = xupper + resargs['xpad']
pylower = ylower - resargs['ypad']
pyupper = yupper + resargs['ypad']

if xrangelims is not None:
    pxlower, pxupper = xrangelims
if yrangelims is not None:
    pylower, pyupper = yrangelims
plt.xlim(pxlower, pxupper)
plt.ylim(pylower, pyupper)

plt.xlabel(xlab)
plt.ylabel(ylab)

central = resargs['central']
ithreshold = resargs['ithresh']
con = resargs['continuum']

maxima = ss.argrelmax(amps)[0]
minima = ss.argrelmin(amps)[0]

plt.plot(wavelengths, amps, color='blue')
for mx in maxima:
    plt.axvline(wavelengths[mx], color='green')
    
maxinten = -1e6
maxintenplace = -1

for mn in minima:
    plt.axvline(wavelengths[mn], color='red')
    plt.axhline(amps[mn], color='brown')
    maxintenplace = mn
    maxinten = amps[mn]

threshv = con + ithreshold / 100.0
sel = amps > threshv
ewpl = np.where(sel)[0]
ewplf = ewpl[0]
ewpll = ewpl[-1]
ewlow = wavelengths[ewplf]
ewhi = wavelengths[ewpll]
plt.axvline(ewlow, color='orange')
plt.axvline(ewhi, color='orange')
ew = np.trapz(amps[ewplf:ewpll]-1.0, wavelengths[ewplf:ewpll]) / (ewhi - ewlow)
print "ew =", ew

plt.legend([legend])

if maxinten > -1e6:
    sel = amps >= maxinten
    mipl = np.where(sel)[0]
    miplf = mipl[0]
    mipll = mipl[-1]
    lhorn = np.trapz(amps[miplf:maxintenplace]-maxinten, wavelengths[miplf:maxintenplace]) / (wavelengths[maxintenplace]-wavelengths[miplf])
    rhorn = np.trapz(amps[maxintenplace:mipll]-maxinten, wavelengths[maxintenplace:mipll]) / (wavelengths[mipll]-wavelengths[maxintenplace])
    print "lhorn =", lhorn, "rhorn =", rhorn, "rat =", rhorn/lhorn
    plt.axvline(wavelengths[sel][0], color='purple')
    plt.axvline(wavelengths[sel][-1], color='purple')

plt.show()