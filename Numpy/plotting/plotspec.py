#! /usr/bin/env python

import argparse
import matplotlib.pyplot as plt
import matplotlib.patches as mptch
import numpy as np
import string
import sys
import os
import os.path
import fakeobs
import datarange
import specdatactrl
import jdate
import calcticks

parsearg = argparse.ArgumentParser(description='Display spectrum with ranges')
parsearg.add_argument('--outfig', type=str, help='Output figure')
parsearg.add_argument('spec', type=str, help='Spectrum file', nargs='+')
parsearg.add_argument('--xlab', type=str, help='Label for X axis', default='Wavelength ($\AA$)')
parsearg.add_argument('--ylab', type=str, help='Label for Y axis', default='Intensity')
parsearg.add_argument('--width', help="Width of plot", type=float, default=8)
parsearg.add_argument('--height', help="Height of plot", type=float, default=6)
parsearg.add_argument('--intranges', help='Ranges to highlight', nargs='*', type=str)
parsearg.add_argument('--title', help='Set window title', type=str, default="Spectrum display")
parsearg.add_argument('--xcolumn', help='Column in data for X values', type=int, default=0)
parsearg.add_argument('--ycolumn', help='Column in data for Y values', type=int, default=1)
parsearg.add_argument('--xrange', help='Range of X values', type=str)
parsearg.add_argument('--yrange', help='Range of Y values', type=str)
parsearg.add_argument('--legnum', type=int, default=5, help='Number of plots in legend')
parsearg.add_argument('--obstimes', type=str, help='File for observation times if not given in files')
parsearg.add_argument('--datefmt', type=str, default='%d/%m/%y %H:%M', help='Format for date display')

resargs = vars(parsearg.parse_args())

spec = resargs['spec']
outfig = resargs['outfig']
xlab = resargs['xlab']
ylab = resargs['ylab']
xcolumn = resargs['xcolumn']
ycolumn = resargs['ycolumn']
legnum = resargs['legnum']
datefmt = resargs['datefmt']

obstimes = dict()
obstimefile = resargs['obstimes']
if obstimefile is not None:
    obstimes = fakeobs.getfakeobs(obstimefile)
    if obstimes is None:
        print "Cannot read obs file", obstimefile
        sys.exit(9)

if xcolumn == ycolumn:
    print "Cannot have X and Y columns the same"
    sys.exit(8)

xrangelims = resargs['xrange']
yrangelims = resargs['yrange']
intrangeargs = resargs['intranges']
intranges = []

try:
    if xrangelims is not None: xrangelims = datarange.ParseArg(xrangelims)
    if yrangelims is not None: yrangelims = datarange.ParseArg(yrangelims)
    if intrangeargs is not None:
        for ir in intrangeargs:
            intranges.append(datarange.ParseArg(ir))
except datarange.DataRangeError as e:
    print e.args[0]
    sys.exit(7)

dims = (resargs['width'], resargs['height'])
fig = plt.figure(figsize=dims)
fig.canvas.set_window_title(resargs['title'])

yupper = -1e6
ylower = 1e6
xupper = -1e6
xlower = 1e6

legends = []
plotlist = []
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
    
    sf = os.path.basename(sf)

    plotlist.append((wavelengths, amps))

    if sf in obstimes:
        dt = jdate.jdate_to_datetime(obstimes[sf])
        legends.append(dt.strftime(datefmt))
    else:
        jd = specdatactrl.jd_parse_from_filename(sf)
        if jd is not None:
            dt = jdate.jdate_to_datetime(jd)
            legends.append(dt.strftime(datefmt))
        else:
            legbits = string.split(sf, '.')
            legends.append(legbits[0])

if xrangelims is not None:
    plt.xlim(xrangelims.lower, xrangelims.upper)
if yrangelims is not None:
    plt.ylim(yrangelims.lower, yrangelims.upper)

ax = plt.gca()
ax.get_xaxis().get_major_formatter().set_useOffset(False)
ax.get_yaxis().get_major_formatter().set_useOffset(False)

for wavelengths,amps in plotlist:
    plt.plot(wavelengths, amps)

ylower, yupper = ax.get_ylim()
for ir in intranges:
    colu = ir.rgbcolour()
    if ir.alpha == 0.0:
        plt.axvline(ir.lower, color=colu)
        plt.axvline(ir.upper, color=colu)
    else:
        p = mptch.Rectangle((ir.lower,ylower), ir.upper-ir.lower, yupper-ylower, color=colu, alpha=ir.alpha)
        ax.add_patch(p)
#ax.canvas.draw()

plt.xlabel(xlab)
plt.ylabel(ylab)

if legnum > 0:
    if len(legends) > legnum:
        legends = legends[0:legnum]
        legends.append("etc...")
    plt.legend(legends)

if outfig is not None:
    plt.savefig(outfig)
else:
    plt.show()
