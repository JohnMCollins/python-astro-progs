#!  /usr/bin/env python3

"""Run through findres files and get best aperture size for each object found"""

import argparse
import warnings
import sys
import re
import pymysql
import numpy as np
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
import miscutils
import remdefaults
import remfits
import find_results

matchname = re.compile('(\w+?)(\d+)$')

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

parsearg = argparse.ArgumentParser(description='Look at find result files and get all best apertures', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', nargs='+', type=str, help='Find results')
remdefaults.parseargs(parsearg, tempdir=False)
parsearg.add_argument('--cutoff', type=float, default=2.0, help='Percentage extra in ring to disreagard')
parsearg.add_argument('--shiftmax', type=int, default=4, help='Maxmimum shift of centre')
parsearg.add_argument('--maxap', type=int, default=20, help='Maximum aperture size to use')
parsearg.add_argument('--minap', type=int, default=3, help='Minimum aperture size to use')
parsearg.add_argument('--update', action='store_true', help='Update apperture in database')
parsearg.add_argument('--verbose', action='store_true', help='Give blow by blow account"')

resargs = vars(parsearg.parse_args())
flist = resargs['files']
remdefaults.getargs(resargs)
cutoff = resargs['cutoff']
shiftmax = resargs['shiftmax']
maxap = resargs['maxap']
minap = resargs['minap']
update = resargs['update']
verbose = resargs['verbose']

mydb, mycurs = remdefaults.opendb()

apsizes = dict()

todo = len(flist)
donef = 0

for ffile in flist:

    donef += 1
    if verbose and donef % 10 == 0:
        print("Done {:d} of {:d} {:.2f}%".format(donef, todo, 100.8 * donef / todo))
    pref = miscutils.removesuffix(ffile, allsuff=True)
    mg = matchname.match(pref)
    if mg is None:
        print("Confused about name", pref, file=sys.stderr)
        continue

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

    for r, offs in zip(rstr.results(), offsets):
        col, row = offs
        if col < 0 or row < 0:
            continue
        if len(r.name) == 0:
            continue
        if r.name not in apsizes:
            apsizes[r.name] = []

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

        if cutoffap < 1000:
            apsizes[r.name].append(cutoffap)

# DB might have gone away

try:
    mydb.close()
except pymysql.Error:
    pass
mydb, mycurs = remdefaults.opendb()

nupdates = 0
for n in sorted(apsizes.keys()):
    lst = apsizes[n]
    if len(lst) == 0:
        print("Unable to get apperture for", n, file=sys.stderr)
        continue
    if min(lst) == max(lst):
        res = lst[0]
    else:
        values, bins = np.histogram(lst, bins=range(min(lst), max(lst) + 1))
        try:
            p = values.argmax()
        except ValueError:
            print("Value error with list for", n, "=", lst, file=sys.stderr)
            continue
        res = bins[p]
    if verbose:
        print("{:<24s} {:4d} {:2d}".format(n, len(lst), res), file=sys.stderr)
    if update:
        nupdates += mycurs.execute("UPDATE objdata SET apsize={:d} WHERE objname=%s".format(res), n)

if nupdates > 0:
    if verbose:
        print(nupdates, "records updated", file=sys.stderr)
    mydb.commit()
