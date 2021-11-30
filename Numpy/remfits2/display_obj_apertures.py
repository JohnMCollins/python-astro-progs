#!  /usr/bin/env python3

"""Run through one findres file and display results of object apertures for target"""

import argparse
import warnings
import sys
import numpy as np
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
import matplotlib.pyplot as plt
import miscutils
import remdefaults
import remfits
import find_results
import remgeom

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

rg = remgeom.load()
parsearg = argparse.ArgumentParser(description='Display results of object apertures', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('file', nargs=1, type=str, help='Find results assume image file same prefix')
parsearg.add_argument('--object', type=str, nargs='+', required=True, help='Objects we are getting aperture for')
rg.disp_argparse(parsearg)
remdefaults.parseargs(parsearg, tempdir=False)
parsearg.add_argument('--shiftmax', type=int, default=4, help='Maxmimum shift of centre')
parsearg.add_argument('--maxap', type=int, default=20, help='Maximum aperture size to use')
parsearg.add_argument('--minap', type=int, default=1, help='Minimum aperture size to use')
parsearg.add_argument('--update', type=int, nargs='+', help='No aperture size for each label 0 to leave same')

resargs = vars(parsearg.parse_args())
prefix = miscutils.removesuffix(resargs['file'][0], 'findres')
targobjs = resargs['object']
rg.disp_getargs(resargs)
remdefaults.getargs(resargs)
shiftmax = resargs['shiftmax']
maxap = resargs['maxap']
minap = resargs['minap']
updateap = resargs['update']

if updateap:
    if  len(updateap) != len(targobjs):
        print("update length", len(updateap), "but object length", len(targobjs), "should be same", file=sys.stderr)
        sys.exit(9)
else:
    updateap = [0] * len(targobjs)

aprange = np.arange(minap, maxap + 1)

try:
    fitsobj = remfits.parse_filearg(prefix, None)
except remfits.RemFitsErr as e:
    print("Error with FITS file", prefix, e.args[0], file=sys.stderr)
    sys.exit(10)
try:
    findres = find_results.load_results_from_file(prefix, fitsobj)
except find_results.FindResultErr as e:
    print("Error with find file", prefix, e.args[0], file=sys.stderr)
    sys.exit(11)

skylevel = fitsobj.meanval
offsets = findres.get_offsets_in_image()

f = rg.plt_figure()

legs = []
changes = 0

for targobj, upap in zip(targobjs, updateap):
    targres = None

    for r, offs in zip(findres.results(), offsets):
        if r.label == targobj:
            targres = r
            col, row = offs
            break

    if targres is None or col < 0 or row < 0:
        print("Could not find", targobj, "in results", file=sys.stderr)
        continue

    adutots = []
    pixes = []
    for ap in aprange:
        optap = findres.findbest_colrow(col, row, ap, shiftmax)
        col, row, aduc, npix = optap
        newadus = aduc - npix * skylevel
        adutots.append(newadus)
        if ap == upap and ap != targres.apsize:
            targres.adus = newadus
            targres.row = row
            targres.col = col
            targres.apsize = ap
            print("Updated", targres.name, file=sys.stderr)
            changes += 1
        pixes.append(npix)
        
    avcont = np.diff(adutots) / np.diff(pixes)
    plt.plot(aprange[1:], avcont)
    legs.append(targobj)

if changes != 0:
    findres.reorder()
    findres.relabel()
    find_results.save_results_to_file(findres, prefix, force=True)

plt.xticks(aprange)
plt.xlabel("Aperture size")
plt.ylabel("AV count")
plt.legend(legs)
plt.show()
