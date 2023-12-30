#!  /usr/bin/env python3

"""Analyse brightest objects in findresult files
SUPERSEDED"""

import argparse
import warnings
import numpy as np
from astropy.utils.exceptions import ErfaWarning
import remdefaults
import find_results
import logs

warnings.simplefilter('ignore', ErfaWarning)

parsearg = argparse.ArgumentParser(description='Analyse find object results', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', nargs='+', type=str, help='Find results file(s)')
remdefaults.parseargs(parsearg, tempdir=False, inlib=False)
parsearg.add_argument('--numobjs', type=int, default=10, help='Number of brightest objects in each')
logs.parseargs(parsearg)

resargs = vars(parsearg.parse_args())
files = resargs['files']
remdefaults.getargs(resargs)
numobjs = resargs['numobjs']
logging = logs.getargs(resargs)

logging.die(200, "This program has been superseded now find result are stored in the database")

mydb, dbcurs = remdefaults.opendb()

resdict = dict()
overlaps = dict()

for fil in files:

    try:
        findres = find_results.load_results_from_file(fil)
    except find_results.FindResultErr as e:
        logging.write(fil, "gave error", e.args[0])
        continue

    n = 0
    cset = set()
    for fr in findres.results():

        if not fr.hide and fr.obj is not None and not fr.obj.valid_label():

            cset.add(fr.obj.objname)
            try:
                resdict[fr.obj.objname].append(n)
            except KeyError:
                resdict[fr.obj.objname] = [n]

        n += 1
        if  n >= numobjs:
            break

    # Build list of positions and appertures

    pixpos = []
    aplist = []
    namelist = []
    for fr in findres.results(idonly=True, nohidden=True):
        pixpos.append(complex(fr.col,fr.row))
        aplist.append(fr.apsize)
        namelist.append(fr.obj.objname)
    distct = np.abs(np.subtract.outer(pixpos, pixpos))
    apcomp = np.add.outer(aplist, aplist)
    overlap_rows, overlap_cols = np.where((distct - apcomp) < 0)

    for row, col in zip(overlap_rows, overlap_cols):
        if row >= col:
            continue
        name1 = namelist[row]
        name2 = namelist[col]
        try:
            s1 = overlaps[name1]
        except KeyError:
            s1 = overlaps[name1] = set()
        try:
            s2 = overlaps[name2]
        except KeyError:
            s2 = overlaps[name2] = set()
        s1.add(name2)
        s2.add(name1)

for name, arr in resdict.items():
    dbcurs.execute("SELECT apsize,gmag,rmag,imag FROM objdata WHERE objname=%s", name)
    r = dbcurs.fetchone()
    if r is None:
        print(name, "(No data)")
    else:
        vv = []
        for val, nm in zip(r, ("ap", "g", "r", "i")):
            if val is not None:
                vv.append("{:s}={:.6g}".format(nm, val))
        print(name, " ".join(vv))
    aarr = np.array(arr)
    for p in range(1, aarr.max()+2):
        nz = np.count_nonzero(aarr==p)
        if nz != 0:
            print("\tPosn {:d}: {:d}".format(p, nz))
    if name in overlaps:
        print("\tOverlaps with\n\t\t", "\n\t\t".join(sorted(overlaps[name])), sep='')
