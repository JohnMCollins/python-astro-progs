#!  /usr/bin/env python3

"""Run through findres files and get best aperture size for each object found"""

import argparse
import warnings
import sys
import re
import os.path
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
import miscutils
import remdefaults
import remfits
import find_results
import apopt

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
parsearg.add_argument('--force', action='store_true', help='Force write to file otherwise skip')
parsearg.add_argument('--verbose', action='store_true', help='Give blow by blow account"')

resargs = vars(parsearg.parse_args())
flist = resargs['files']
remdefaults.getargs(resargs)
cutoff = resargs['cutoff']
shiftmax = resargs['shiftmax']
maxap = resargs['maxap']
minap = resargs['minap']
force = resargs['force']
verbose = resargs['verbose']

mydb, mycurs = remdefaults.opendb()

todo = len(flist)
donef = 0

for ffile in flist:

    donef += 1
    if verbose and donef % 10 == 0:
        print("Doing {:d} of {:d} {:.2f}%".format(donef, todo, (100.0 * donef) / todo))
    pref = miscutils.removesuffix(ffile, allsuff=True)
    mg = matchname.match(pref)
    if mg is None:
        print("Confused about name", pref, file=sys.stderr)
        continue

    apoptfile = remdefaults.apopt_file(pref)
    if not force and os.path.exists(apoptfile):
        if verbose:
            print("Skipping existing", apoptfile, file=sys.stderr)
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
    apsizes = dict()

    for r, offs in zip(rstr.results(), offsets):
        if r.objident is None:
            continue
        col, row = offs
        if col < 0 or row < 0:
            continue

        prevextra = 0
        prevnpix = 0
        aps = []
        adus = []
        extraaduav = []
        cutoffap = 1000000
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

        if cutoffap < 1000:
            apsizes[r.objident.objname] = (cutoffap, r.objident.objind)

    if len(apsizes) == 0:
        if verbose:
            print("No results found in", pref, "skipping", file=sys.stderr)
        continue

    resultfile = apopt.ApOptResults()
    resultfile.obsdate = rstr.obsdate
    resultfile.filter = rstr.filter
    resultfile.obsind = rstr.obsind
    resultfile.cuttoff = cutoff

    for obj_name, (aos, ind) in apsizes.items():
        resultfile.resultlist.append(apopt.ApOpt(apsize=aos, objind=ind, objname=obj_name))

    try:
        apopt.save_apopts_to_file(resultfile, apoptfile, force)
        if verbose:
            print(ffile, "completed", file=sys.stderr)
    except apopt.ApOptErr as e:
        print("Save apopt results failed", e.args[0], file=sys.stderr)
