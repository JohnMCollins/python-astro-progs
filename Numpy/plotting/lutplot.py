#! /usr/bin/env python

import sys
import math
import numpy as np
import matplotlib.pyplot as plt
import argparse
import string

import lutdata

parsearg = argparse.ArgumentParser(description='Display segments of LUT file')
parsearg.add_argument('--lutfile', type=argparse.FileType('r'), help='Input LUT file')
parsearg.add_argument('--basewl', type=float, default=6562.8, help='Base wavelength')
parsearg.add_argument('--outfile', type=str, help='Output file if required')
parsearg.add_argument('points', type=str, nargs='+', help='Points to display of form tempnumber:index')

resargs = vars(parsearg.parse_args())

inf = resargs['lutfile']
basewl = resargs['basewl']
pts = resargs['points']

ld = lutdata.Lutdata()
ld.loaddata(inf)
inf.close()
da = ld.dataarray
la = ld.langles

temp1 = round(ld.mint4 ** .25, 2)
temp2 = round(((ld.maxt4+ld.mint4) / 2.0) ** .25, 2)
temp3 = round(ld.maxt4 ** .25, 2)
temps = (temp1, temp2, temp3)

minlambda = basewl * (1.0 + ld.minv / 299792.458)
maxlambda = basewl * (1.0 + ld.maxv / 299792.458)
lambdarange = maxlambda - minlambda

#print "Temps: 1: %.2f 2: %.2f 3: %.2f" % temps
#print "Min/max lambda = %.2f %.2f" % (minlambda, maxlambda)

plt.xlabel('Cosine limb angle')
plt.ylabel('Intensity')
for pt in pts:
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
