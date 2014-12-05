#! /usr/bin/python

import argparse
import matplotlib.pyplot as plt
import numpy as np
import string
import sys
import os
import rangearg
import calcticks

parsearg = argparse.ArgumentParser(description='Display spectrum with ranges')
parsearg.add_argument('--outfig', type=str, help='Output figure')
parsearg.add_argument('spec', type=str, help='Spectrum file', nargs='+')
parsearg.add_argument('--xlab', type=str, help='Label for X axis', default='Wavelength Angstroms')
parsearg.add_argument('--ylab', type=str, help='Label for Y axis', default='Intensity')
parsearg.add_argument('--fork', action='store_true', help='Fork off daemon process to show plots and exit')
parsearg.add_argument('--width', help="Width of plot", type=float, default=8)
parsearg.add_argument('--height', help="Height of plot", type=float, default=6)
parsearg.add_argument('--xpad', help='Padding round x', type=float, default=.25)
parsearg.add_argument('--ypad', help='Padding round y', type=float, default=.01)
parsearg.add_argument('--lower', help='Lower integration range', type=float,default=0)
parsearg.add_argument('--upper', help='Upper integration range', type=float,default=0)
parsearg.add_argument('--intrange', help='Integration range as nnn,nnn', type=str)
parsearg.add_argument('--title', help='Set window title', type=str, default="Spectrum display")
parsearg.add_argument('--linecolour', help='Set line colour for range', type=str, default='black')
parsearg.add_argument('--xcolumn', help='Column in data for X values', type=int, default=0)
parsearg.add_argument('--ycolumn', help='Column in data for Y values', type=int, default=1)
parsearg.add_argument('--xrange', help='Range of X values', type=str)
parsearg.add_argument('--xlower', help='Lower limit of x', type=float, default=0)
parsearg.add_argument('--xupper', help='Upper limit of x', type=float, default=0)

resargs = vars(parsearg.parse_args())

spec = resargs['spec']
outfig = resargs['outfig']
xlab = resargs['xlab']
ylab = resargs['ylab']
forkoff = resargs['fork']
xcolumn = resargs['xcolumn']
ycolumn = resargs['ycolumn']
xrangelims = rangearg.getrangearg(resargs, rangename='xrange', lowerarg='xlower', upperarg='xupper')

if xcolumn == ycolumn:
    print "Cannot have X and Y columns the same"
    sys.exit(8)

plt.rcParams['figure.figsize'] = (resargs['width'], resargs['height'])
fig = plt.gcf()
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

    plotlist.append((wavelengths, amps))

    yupper = max(yupper, np.max(amps))
    ylower = min(ylower, np.min(amps))
    xupper = max(xupper, np.max(wavelengths))
    xlower = min(xlower, np.min(wavelengths))

    legbits = string.split(sf, '.')
    legends.append(legbits[0])

xlower -= resargs['xpad']
xupper += resargs['xpad']
ylower -= resargs['ypad']
yupper += resargs['ypad']

if xrangelims[0] != 0.0:
    xlower = xrangelims[0]
if xrangelims[1] != 0.0:
    xupper = xrangelims[1]
plt.xlim(xlower, xupper)
plt.ylim(ylower, yupper)
try:
    lline, uline = rangearg.getrangearg(resargs, rangename='intrange')
except ValueError:
    lline = uline = 0.0

linecol = resargs['linecolour']

if lline > 0.0:
    plt.axvline(x=lline, ymin=0, ymax=yupper, color=linecol, label='Lower')
if uline > 0.0:
    plt.axvline(x=uline, ymin=0, ymax=yupper, color=linecol, label='Upper')

xt, xtl = calcticks.calcticks(resargs['width'], xlower, xupper)
plt.xticks(xt, xtl)
plt.xlabel(xlab)
plt.ylabel(ylab)

for wavelengths,amps in plotlist:
    plt.plot(wavelengths, amps)

if len(legends) > 5:
    legends = legends[0:5]
    legends.append("etc...")
plt.legend(legends, loc='upper left')

if outfig is not None:
    plt.savefig(outfig)
if not forkoff or os.fork() == 0:
    plt.show()

