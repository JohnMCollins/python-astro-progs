#!  /usr/bin/env python3

"""Display findresult file"""

import argparse
import sys
import warnings
from astropy.utils.exceptions import ErfaWarning, AstropyWarning, AstropyUserWarning
import astroquery.utils as autils
import numpy as np
import remdefaults
import find_results
import remfits

warnings.simplefilter('ignore', ErfaWarning)
warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)
autils.suppress_vo_warnings()

parsearg = argparse.ArgumentParser(description='Go through findres file try to find image offset', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('file', nargs=1, type=str, help='Image file')
remdefaults.parseargs(parsearg, tempdir=False, inlib=False)
parsearg.add_argument('--findres', type=str, help='Findres file if different')
parsearg.add_argument('--maxshift', type=int, default=3, help='Maximum shift')
parsearg.add_argument('--totsign', type=float, default=.5, help='Total significance')
parsearg.add_argument('--weighting', type=float, default=1.0, help='Weighting factor')
parsearg.add_argument('--select', type=int, default=10, help='Number of objects to select')

resargs = vars(parsearg.parse_args())
fitsfile = resargs['file'][0]
remdefaults.getargs(resargs)
frfile = resargs['findres']
maxshift = resargs['maxshift']
totsig = resargs['totsign']
weighting = resargs['weighting']
selectn = resargs['select']

try:
    robj = remfits.parse_filearg(fitsfile, None)
except remfits.RemFitsErr as e:
    print("Cannot open", fitsfile, "error was", e.args[0], file=sys.stderr)
    sys.exit(10)

if frfile is None:
    frfile = fitsfile

try:
    findres = find_results.load_results_from_file(frfile, robj)
except find_results.FindResultErr as e:
    print("Cannot open", frfile, "error was", e.args[0], file=sys.stderr)
    sys.exit(11)

if findres.num_results(idonly=True) == 0:
    print("No identified results in", frfile, file=sys.stderr)
    sys.exit(12)

positions = [complex(f.row, f.col) for f in findres.results(idonly=True)]
labs = [f.label for f in findres.results(idonly=True)]
if len(labs) < selectn:
    print("Not enough objects", len(labs), "requiring", selectn, file=sys.stderr)
    sys.exit(13)

difftab = np.abs(np.subtract.outer(positions, positions))
for n in range(0, difftab.shape[0]):
    difftab[n, n] = 1000000
minima = difftab.min(axis=1)
gorder = (-minima).argsort()[:selectn]

offd = dict()
for g in gorder:
    res = findres[labs[g]]
    apwidth = res.obj.apsize
    if apwidth == 0:
        apwidth = res.apsize
    res.obj.apply_motion(findres.obsdate)
    offlist = findres.find_object_offsets(res.obj, maxshift, totsig, apwidth)
    if offlist is None:
        print("No find results for", res.obj.dispname, file=sys.stderr)
        continue
    wt = 1.0
    startw = offlist[0][-1]
    for roff, coff, row, col, adus in offlist:
        w = (roff, coff)
        iwt = wt * adus / startw
        try:
            offd[w] += wt
        except KeyError:
            offd[w] = wt
        wt *= weighting

koccs = sorted(offd.keys(), key=lambda x:-offd[x])
for k in koccs:
    print(k, offd[k])
