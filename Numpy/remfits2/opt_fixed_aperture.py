#!  /usr/bin/env python3

from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
from astropy.io import fits
from astropy.time import Time
import datetime
import numpy as np
import argparse
import warnings
import sys
import miscutils
import math
import remdefaults
import remfits
import os.path
import find_results

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

rg = remgeom.load()
parsearg = argparse.ArgumentParser(description='Refine object apertures in image ', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', nargs=2, type=str, help='Image file and find results')
rg.disp_argparse(parsearg)
remdefaults.parseargs(parsearg, tempdir=False)
# parsearg.add_argument('--force', action='store_true', help='Force overwrite of existing file')
parsearg.add_argument('--cutoff', type=float, default=2.0, help='Percentage extra in ring to disreagard')
parsearg.add_argument('--shiftmax', type=int, default=4, help='Maxmimum shift of centre')
parsearg.add_argument('--maxap', type=int, default=20, help='Maximum aperture size to use')
parsearg.add_argument('--minap', type=int, default=3, help='Minimum aperture size to use')
parsearg.add_argument('--plot', action='store_false', help='Plot results')

resargs = vars(parsearg.parse_args())
infile, resfile = resargs['files']
rg.disp_getargs(resargs)
remdefaults.getargs(resargs)
cutoff = resargs['cutoff']
shiftmax = resargs['shiftmax']
maxap = resargs['maxap']
minap = resargs['minap']
resfile = remdefaults.libfile(resfile)
doplot = resargs['plot']

mydb, dbcurs = remdefaults.opendb()

try:
    inputfile = remfits.parse_filearg(infile, dbcurs)
except remfits.RemFitsErr as e:
    print(e.args[0], file=sys.stderr)
    sys.exit(52)

try:
    rstr = find_results.load_results_from_file(resfile, inputfile)
except find_results.FindResultErr as e:
    print(e.args[0], file=sys.stderr)
    sys.exit(100)

skylevel = inputfile.meanval
changes = 0

offsets = rstr.get_offsets_in_image()
for r, offs in zip(rstr.results(), offsets):
    col, row = offs
    if col < 0 or row < 0:
        continue
    if len(r.name) != 0:
        print(r.name, end=":\n")
    else:
        print(r.label, end=":\n")
    prevextra = 0
    prevnpix = 0
    aps = []
    adus = []
    extraaduav = []
    cutoffap = 100
    cutoffrow = cutoffcol = cutoffadu = -1
    for ap in range(minap, maxap + 1):
        optap = rstr.findbest_colrow(col, row, ap, shiftmax)
        col, row, aduc, npix = optap
        adus_sofar = aduc - npix * skylevel
        xtra = adus_sofar - prevextra
        pc = 100 * xtra / adus_sofar
        print("\t", "%2d %3d %3d%10.2f%5d%5d%10.2f%10.2f%8.2f" % (ap, col, row, aduc, int(npix), int(npix - prevnpix), adus_sofar, xtra, float(pc)), sep='')
        prevextra = adus_sofar
        prevnpix = npix
        aps.append(ap)
        adus.append(adus_sofar)
        extraaduav.append(pc)
        if pc < cutoff and ap < cutoffap:
            cutoffap = ap
            cutoffrow = row
            cutoffcol = col
            cutoffadu = aduc
    if doplot:
        f = rg.plt_figure()
        plt.plot(aps, adus)
        plt.xlabel("Aperture size")
        plt.ylabel("ADU count over sky level (" + r.label + ")")
        ax = plt.gca().twinx()
        plt.plot(aps, extraaduav, color='r')
        plt.ylabel("Av extra from additional ring")
        plt.axhline(cutoff, color='k')
        plt.axvline(cutoffap, color='k')
    print("Cutoff at", cutoffap)
    if r.apsize != cutoffap:
        changes += 1
        r.apsize = cutoffap
        r.row = cutoffrow
        r.col = cutoffcol
        r.adus = cutoffadu

if changes > 0:
    print(changes, "changes")
    rstr.calccoords()
    find_results.save_results_to_file(rstr, resfile, force=True)

if doplot:
    plt.show()
