#! /usr/bin/env python

import sys
import math
import numpy as np
import matplotlib.pyplot as plt
import argparse
import string

import lutdata

parsearg = argparse.ArgumentParser(description='Display segments of LUT file')
parsearg.add_argument('args', type=str, nargs='+', help='LUT file optionally followed by point args')
parsearg.add_argument('--basewl', type=float, default=6562.8, help='Base wavelength for when picking single wavelengths out')
parsearg.add_argument('--outfile', type=str, help='Output file if required')
parsearg.add_argument('--width', type=float, help='Width of figure', default=8.0)
parsearg.add_argument('--height', type=float, help='Height of figure', default=6.0)

resargs = vars(parsearg.parse_args())

args = resargs['args']

lutf = args.pop(0)
try:
    inf = open(lutf, 'r')
except IOError as e:
    print "Could not open", lutf, "error was", e.args[1]
    sys.exit(10)

ld = lutdata.Lutdata()
ld.loaddata(inf)
inf.close()
da = ld.dataarray
la = ld.langles

temp1 = round(ld.mint4 ** .25, 2)
temp2 = round(((ld.maxt4+ld.mint4) / 2.0) ** .25, 2)
temp3 = round(ld.maxt4 ** .25, 2)
temps = (temp1, temp2, temp3)

#print "Temps: 1: %.2f 2: %.2f 3: %.2f" % temps
#print "Min/max lambda = %.2f %.2f" % (minlambda, maxlambda)

plt.rcParams['figure.figsize'] = (resargs['width'], resargs['height'])

plt.xlabel('Cosine limb angle')
plt.xlim(0,1)
plt.ylabel('Intensity')
if len(args) == 0:
    tempcols = ['red','black','blue']
    plt.ylim(da.min(), da.max())
    for tr in da:
        clr = tempcols.pop(0)
        for wl in tr:
            plt.scatter(la, wl, color=clr)
else:
    basewl = resargs['basewl']
    minlambda = basewl * (1.0 + ld.minv / 299792.458)
    maxlambda = basewl * (1.0 + ld.maxv / 299792.458)
    lambdarange = maxlambda - minlambda
    for pt in args:
        bits = string.split(pt, ':')
        if len(bits) > 2:
            print "Cannot understand argument", pt
            continue
        try:
            if len(bits) == 2:
                req = [False] * 3
                for r in [int(x)-1 for x in bits[0]]: req[r] = True
                wl = float(bits[1])
            else:
                req = [True] * 3
                wl = float(pt)
        except ValueError, IndexError:
            print "Did not understand point", pt
            continue
        if not (minlambda <= wl <= maxlambda):
            print "Wavelength", wl, "not in range", round(minlambda, 2), "to", round(maxlambda, 2)
            continue
        indx = int(round(((wl - minlambda) / lambdarange) * ld.nvels))
        for i in range(0, 3):
            if req[i]:
                plt.plot(la, da[i][indx], label="%.0f$^\circ$ $\lambda$=%.2f" % (temps[i], wl))
        plt.legend()

outf = resargs['outfile']
if outf is not None:
    try:
        plt.savefig(outf)
        sys.exit(0)
    except IOError as e:
        print "Could not save to", outf, "error was", e.args[1]
        sys.exit(30)
try:
    plt.show()
except KeyboardInterrupt:
    pass
