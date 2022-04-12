#!  /usr/bin/env python3

"""Display overlaps in find results"""

import argparse
import sys
import numpy as np
import remdefaults
import find_results
import objdata


def pobj(ind):
    """Display details of object indexed by index"""
    row, col, ap, lab = frlist[ind]
    fr = findres[lab]
    robj = fr.obj
    print(lab, ": ", robj.dispname, " ", fr.rdiff, " ", fr.cdiff, sep='', end='')
    if fr.apsize == 0:
        print(" Undefined aperture", end='')
    print()


parsearg = argparse.ArgumentParser(description='Display overlaps in find results', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', nargs='+', type=str, help='Find results files')
remdefaults.parseargs(parsearg, tempdir=False, inlib=False)
parsearg.add_argument('--filter', type=str, help='Filter name to restrict to')
parsearg.add_argument('--autohide', action='store_true', help='Auto-hide overlapping results')
parsearg.add_argument('--byrc', action='store_true', help='Sort by row then column other than descending brightness')

resargs = vars(parsearg.parse_args())
files = resargs['files']
remdefaults.getargs(resargs)
filt = resargs['filter']
byrc = resargs['byrc']
autohide = resargs['autohide']

foundcount = dict()
objdets = dict()
dispnames = dict()

noverlaps = 0

for fil in files:
    try:
        findres = find_results.load_results_from_file(fil)
    except find_results.FindResultErr as e:
        print(fil, "gave error", e.args[0], file=sys.stderr)
        continue
    if filt and filt != findres.filter:
        print("Skipping", fil, "as filter was", findres.filter)
        continue

    # Build list of things we haven't hidden already
    # Sort by row, column to make them easier to follow

    if byrc:
        frlist = sorted([(fr.row, fr.col, fr.apsize, fr.label) for fr in findres.results() if not fr.hide], key=lambda x: x[0] * 10000 + x[1])
    else:
        frlist = [(fr.row, fr.col, fr.apsize, fr.label) for fr in findres.results() if not fr.hide]

    if len(frlist) == 0:
        print(fil, "has no non-hidden results in", file=sys.stderr)
        continue

    # Build cross-table of distances

    pixpos = np.array([complex(fr[1], fr[0]) for fr in frlist])
    distct = np.abs(np.subtract.outer(pixpos, pixpos))
    aplist = [fr[2] for fr in frlist]
    apcomp = np.add.outer(aplist, aplist)
    rows, cols = np.where((distct - apcomp) < 0)
    lastrow = -1
    hidden = 0
    errors = 0
    for row, col in zip(rows, cols):
        if row >= col:
            continue
        if row != lastrow:
            pobj(row)
            robj = findres[frlist[row][-1]]
            if robj.hide:
                continue
            if robj.apsize == 0:
                errors += 1
        cobj = findres[frlist[col][-1]]
        if cobj.hide:
            continue
        noverlaps += 1
        print("\tClashes with ", end='')
        pobj(col)
        if autohide:
            hidden += 1
            cobj.hide = True
    if hidden > 0:
        if errors != 0:
            print("Not saving as default aperture in", errors, "cases")
        else:
            find_results.save_results_to_file(findres, fil, force=True)

if noverlaps > 0:
    sys.exit(1)
sys.exit(0)
