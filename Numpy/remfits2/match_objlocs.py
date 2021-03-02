#!  /usr/bin/env python3

"""Match locations of objects and find results"""

import argparse
import warnings
import sys
import remdefaults
import obj_locations
import find_results
import match_finds
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

parsearg = argparse.ArgumentParser(description='Match locations of objects within image and find object results', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', nargs='+', type=str, help='Location file and find results file (or just one if same name)')
remdefaults.parseargs(parsearg, tempdir=False)
parsearg.add_argument('--threshold', type=float, default=20.0, help='Threshold for match in arcsec')
parsearg.add_argument('--verbose', action='store_true', help='Give statistics')
parsearg.add_argument('--idonly', action='store_true', help='Just keep things that have been identified')
parsearg.add_argument('--usonly', action='store_true', help='Just keep things that are usable')

resargs = vars(parsearg.parse_args())
files = resargs['files']
remdefaults.getargs(resargs)
threshold = resargs['threshold']
verbose = resargs['verbose']
idonly = resargs['idonly']
usonly = resargs['usonly']

locfile = files[0]
if len(files) > 1:
    if len(files) > 2:
        print("Only expecting at most two files", file=sys.stderr)
        sys.exit(10)
    findresfile = files[1]
else:
    findresfile = locfile + ""  # Forces new copy

locations = obj_locations.load_objlist_from_file(locfile)
findres = find_results.load_results_from_file(findresfile)

try:
    matchlist = match_finds.allocate_locs(locations, findres, threshold)
except match_finds.FindError as e:
    print("Match gave error", e.args[0], file=sys.stderr)
    sys.exit(200)

locr = locations.resultlist
findr = findres.resultlist

hadt = 0

for row, col, dist in matchlist:
    f = findr[col]
    l = locr[row]
    f.name = l.name
    f.dispname = l.dispname
    f.istarget = l.istarget
    if f.istarget:
        hadt += 1
    f.invented = l.invented
    f.isusable = l.isusable
    f.apsize = l.apsize

if hadt != 1:
    print("Did not find a target", file=sys.stderr)
    sys.exit(240)

if idonly or usonly:
    noid = nouse = 0
    newf = []
    for fr in findr:
        if idonly and len(fr.name) == 0:
            noid += 1
        elif usonly and not fr.usable:
            nouse += 1
        else:
            newf.append(fr)
    if nouse + noid > 0:
        findres.resultlist = newf
        if verbose:
            if nouse > 0:
                print(nouse, "not usable eliminated", file=sys.stderr)
            if noid > 0:
                print(noid, "not identified eliminated", file=sys.stderr)

if len(findres.resultlist) < 2:
    print("No results in file other than target", file=sys.stderr)
    sys.exit(241)

findres.reorder()
findres.relabel()
find_results.save_results_to_file(findres, findresfile, True)

if verbose:
    n = nfound = 0
    for f in findres.results():
        n += 1
        if len(f.name) != 0:
            nfound += 1
    print(nfound, "found out of", n, file=sys.stderr)
