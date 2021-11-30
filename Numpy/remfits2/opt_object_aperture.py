#!  /usr/bin/env python3

"""Run through findres files and get best aperture size for target"""

import argparse
import warnings
import sys
import re
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
import matplotlib.pyplot as plt
import miscutils
import remdefaults
import remfits
import find_results
import remgeom
import objdata

matchname = re.compile('(\w+?)(\d+)$')

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

rg = remgeom.load()
parsearg = argparse.ArgumentParser(description='Look at results and list optimal apertures', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', nargs='+', type=str, help='Find results')
parsearg.add_argument('--object', type=str, required=True, help='Object we are getting aperture for')
rg.disp_argparse(parsearg)
remdefaults.parseargs(parsearg, tempdir=False)
parsearg.add_argument('--cutoff', type=float, default=2.0, help='Percentage extra in ring to disreagard')
parsearg.add_argument('--shiftmax', type=int, default=4, help='Maxmimum shift of centre')
parsearg.add_argument('--maxap', type=int, default=20, help='Maximum aperture size to use')
parsearg.add_argument('--minap', type=int, default=3, help='Minimum aperture size to use')
parsearg.add_argument('--plotopt', action='store_true', help='Plot optimisation (do not use if lots)')

resargs = vars(parsearg.parse_args())
flist = resargs['files']
targobj = resargs['object']
rg.disp_getargs(resargs)
remdefaults.getargs(resargs)
cutoff = resargs['cutoff']
shiftmax = resargs['shiftmax']
maxap = resargs['maxap']
minap = resargs['minap']
doplot = resargs['plotopt']

mydb, mycurs = remdefaults.opendb()

try:
    targobj = objdata.get_objname(mycurs, targobj)
except objdata.ObjDataError as e:
    print("Trouble with", targobj, e.args[0], file=sys.stderr)
    sys.exit(10)

apsizes = []
filt_apsizes = dict(g=[], i=[], r=[], z=[])

for ffile in flist:

    pref = miscutils.removesuffix(ffile, allsuff=True)
    mg = matchname.match(pref)
    if mg is None:
        print("Confused about name", imnumb, file=sys.stderr)
        continue
    imnumb = int(mg.group(2))

    try:
        imageff = remfits.parse_filearg(pref, mycurs)
    except remfits.RemFitsErr as e:
        print(e.args[0], file=sys.stderr)
        continue
    try:
        rstr = find_results.load_results_from_file(pref, imageff)
    except find_results.FindResultErr as e:
        print(e.args[0], file=sys.stderr)
        continue

    skylevel = imageff.meanval
    offsets = rstr.get_offsets_in_image()

    targres = None

    for r, offs in zip(rstr.results(), offsets):
        if r.name == targobj:
            targres = r
            col, row = offs
            break

    if targres is None or col < 0 or row < 0:
        apsizes.append(0)
        filt_apsizes[rstr.filter].append(0)
        continue

    prevextra = 0
    prevnpix = 0
    aps = []
    adus = []
    extraaduav = []
    cutoffap = 1000000
    cutoffrow = cutoffcol = cutoffadu = -1
    for ap in range(minap, maxap + 1):
        optap = rstr.findbest_colrow(col, row, ap, shiftmax)
        col, row, aduc, npix = optap
        adus_sofar = aduc - npix * skylevel
        xtra = adus_sofar - prevextra
        pc = 100 * xtra / adus_sofar
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
        binr = range(min(aps), max(aps) + 1)
        plt.xticks(binr)
        plt.plot(aps, adus)
        plt.xlabel("Aperture size ({:s} filter based on obsind {:d})".format(rstr.filter, imnumb))
        plt.ylabel("ADU count over sky level (" + targres.label + ")")
        ax = plt.gca().twinx()
        plt.plot(aps, extraaduav, color='r')
        plt.ylabel("Av extra from additional ring")
        plt.axhline(cutoff, color='k')
        plt.axvline(cutoffap, color='k')

    if cutoffap < 1000:
        print(imnumb, cutoffap, sep=':')
        apsizes.append(cutoffap)
        filt_apsizes[rstr.filter].append(cutoffap)
    else:
        print(imnumb, targobj, "not found")
        apsizes.append(0)

f = rg.plt_figure()
binr = range(min(apsizes), max(apsizes) + 2)
plt.xlabel("Best aperture size (all filters) for " + targobj)
plt.ylabel("Times best aperture")
plt.xticks(binr)
hr = plt.hist(apsizes, bins=binr, rwidth=0.4, align='left')
if binr[0] == 0:
    hr[2][0].set_facecolor('r')

f = rg.plt_figure()

for filt, subp in ('i', 221), ('g', 222), ('z', 223), ('r', 224):
    plt.subplot(subp)
    aps = filt_apsizes[filt]
    if len(aps) == 0:
        continue
    binr = range(min(aps), max(aps) + 2)
    plt.xlabel("Best aperture size (" + filt + " filter) for " + targobj)
    plt.ylabel("Times best aperture")
    plt.xticks(binr)
    hr = plt.hist(aps, bins=binr, rwidth=0.4, align='left')
    if binr[0] == 0:
        hr[2][0].set_facecolor('r')

plt.show()
