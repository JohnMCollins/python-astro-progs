#! /usr/bin/env python

import argparse
import matplotlib.pyplot as plt
import matplotlib.patches as mptch
import numpy as np
import scipy.interpolate as sint
import string
import sys
import os
import os.path
import datarange
import specdatactrl
import specinfo
import jdate

lslu = dict(solid = '.', dashed = '--', dashdot = '-.', dotted = ':')

parsearg = argparse.ArgumentParser(description='Display spectra with ranges from info file')
parsearg.add_argument('--infofile', type=str, required=True, help='Info file giving spectra')
parsearg.add_argument('--outfig', type=str, help='Output figure')
parsearg.add_argument('spec', type=int, help='Spectrum selection', nargs='+')
parsearg.add_argument('--xlab', type=str, help='Label for X axis', default='Wavelength ($\AA$)')
parsearg.add_argument('--ylab', type=str, help='Label for Y axis', default='Intensity')
parsearg.add_argument('--width', help="Width of plot", type=float, default=8)
parsearg.add_argument('--height', help="Height of plot", type=float, default=6)
parsearg.add_argument('--intranges', help='Ranges to highlight', nargs='*', type=str)
parsearg.add_argument('--title', help='Set window title', type=str, default="Spectrum display")
parsearg.add_argument('--plotcolours', type=str, default='b,g,r,c,y,m,k', help='Cycle of colours for plot')
parsearg.add_argument('--linecolour', type=str, help='Colour to force range lines')
parsearg.add_argument('--linestyle', type=str, default='-', help='Line style for range lines')
parsearg.add_argument('--xrange', help='Range of X values', type=str)
parsearg.add_argument('--yrange', help='Range of Y values', type=str)
parsearg.add_argument('--legnum', type=int, default=5, help='Number of plots in legend')
parsearg.add_argument('--datefmt', type=str, default='%d/%m/%y %H:%M', help='Format for date display')
parsearg.add_argument('--linemk', type=str, nargs='+', help='Lines to mark as wl:label:colour:xoff:yoff:rotdeg:style')
parsearg.add_argument('--subspec', type=int, help='Subtract given spectrum number from display')
parsearg.add_argument('--divspec', type=int, help='Divide given spectrum number from display')
parsearg.add_argument('--raw', action='store_true', help='Skip all scaling and normalisation on Y axis')

resargs = vars(parsearg.parse_args())

infofile = resargs['infofile']
spec = resargs['spec']
plotc = string.split(resargs['plotcolours'], ',')
while len(plotc) < len(spec):
    plotc *= 2
linecolour = resargs['linecolour']
linestyle = resargs['linestyle']
outfig = resargs['outfig']
xlab = resargs['xlab']
ylab = resargs['ylab']
legnum = resargs['legnum']
datefmt = resargs['datefmt']

xrangelims = resargs['xrange']
yrangelims = resargs['yrange']
intrangeargs = resargs['intranges']

linemarks = resargs['linemk']
linmk = []
if linemarks is not None:
    for lm in linemarks:
        lmparts = string.split(lm, ':')
        try:
            if len(lmparts) != 7:
                raise ValueError("Not enough parts of line label")
            wl, lab, lcol, toff, ty, trot, sty = lmparts
            wl = float(wl)
            toff = float(toff)
            ty = float(ty)
            trot = float(trot)
            sty = lslu[string.lower(sty)]
            linmk.append((wl, lab, lcol, toff, ty, trot, sty))
        except KeyError:
            sys.stdout = sys.stderr
            print "Unknown line style", sty, "in", lm
            sys.exit(30)
        except ValueError:
            sys.stdout = sys.stderr
            print "Cannot decode lime spec", lm
            sys.exit(30)

subspec = resargs['subspec']
divspec = resargs['divspec']

if subspec is not None and divspec is not None:
    sys.stdout = sys.stderr
    print "Cannot have beth subspec and divspec"
    sys.exit(31)

if not os.path.isfile(infofile):
    infofile = miscutils.replacesuffix(infofile, specinfo.SUFFIX)

try:
    inf = specinfo.SpecInfo()
    inf.loadfile(infofile)
    rlist = inf.get_rangelist()
    cfile = inf.get_ctrlfile()
except specinfo.SpecInfoError as e:
    sys.stdout = sys.stderr
    print "Cannot load info file", infofile
    print "Error was:", e.args[0]
    sys.exit(10)

try:
    if xrangelims is None:
        xrangelims = rlist.getrange('xrange')
    else:
        xrangelims = datarange.ParseArg(xrangelims)
    if xrangelims.notused:
        xrangelims = None
    if yrangelims is None:
        yrangelims = rlist.getrange('yrange')
    else:
        yrangelims = datarange.ParseArg(yrangelims)
    if yrangelims.notused:
        yrangelims = None
except datarange.DataRangeError as e:
    sys.stdout = sys.stderr
    print e.args[0]
    sys.exit(7)

intranges = []
if intrangeargs is not None:
    for ir in intrangeargs:
        try:
            intranges.append(rlist.getrange(ir))
        except datarange.DataRangeError:
            try:
                intranges.append(datarange.ParseArg(ir))
            except datarange.DataRangeError as e:
                sys.stdout = sys.stderr
                print "Trouble with range arg"
                print "Error was:", e.args[0]
                sys.exit(11)

dims = (resargs['width'], resargs['height'])
fig = plt.figure(figsize=dims)
fig.canvas.set_window_title(resargs['title'])

legends = []
plotlist = []
cfile.loadfiles()

exspec = subspec
if exspec is None: exspec = divspec
ifunc = None

# Select the required routine

yfetch = specdatactrl.SpecDataArray.get_yvalues
if resargs['raw']:
    yfetch = specdatactrl.SpecDataArray.get_raw_yvalues

if exspec is not None:
    try:
        ef = cfile.datalist[exspec]
        exx = ef.get_xvalues()
        exy = yfetch(ef)
    except IndexError:
        sys.stdout = sys.stderr
        print "Invalid sub/div spectrum"
        sys.exit(12)
    except specinfo.SpecInfoError:
        sys.stdout = sys.stderr
        print "Invalid spectrum number", exspec
        sys.exit(12)
    ifunc=sint.interp1d(exx, exy, fill_value=exy[0], bounds_error=False)
        
for sf in spec:
    try:
        df = cfile.datalist[sf]
    except IndexError:
        sys.stdout = sys.stderr
        print "Invalid spectrum index", sf
        sys.exit(20)

    wavelengths = df.get_xvalues()
    amps = yfetch(df)
    if ifunc is not None:
        adjamps = ifunc(wavelengths)
        if divspec is None:
            amps -= adjamps - 1.0
        else:
            amps /= adjamps
    
    plotlist.append((wavelengths, amps, plotc.pop(0)))

    dt = jdate.jdate_to_datetime(df.modjdate)
    legends.append(dt.strftime(datefmt))

if xrangelims is not None:
    plt.xlim(xrangelims.lower, xrangelims.upper)
if yrangelims is not None:
    plt.ylim(yrangelims.lower, yrangelims.upper)

ax = plt.gca()
ax.get_xaxis().get_major_formatter().set_useOffset(False)
ax.get_yaxis().get_major_formatter().set_useOffset(False)

for wavelengths,amps,c in plotlist:
    plt.plot(wavelengths, amps, color=c)

ylower, yupper = ax.get_ylim()
for ir in intranges:
    colu = ir.rgbcolour()
    if ir.alpha == 0.0:
        if linecolour is not None: colu = linecolour
        plt.axvline(ir.lower, color=colu, ls=linestyle)
        plt.axvline(ir.upper, color=colu, ls=linestyle)
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

for lm in linmk:
    wl, lab, lcol, toff, ty, trot, sty = lm
    plt.axvline(wl, ls=sty, color=lcol)
    plt.text(wl, ty, lab, color=lcol, rotation=trot)

if outfig is not None:
    plt.savefig(outfig)
else:
    plt.show()
