#!  /usr/bin/env python3

"""Match locations of objects and find results"""

import argparse
import warnings
import sys
import remdefaults
import obj_locations
import find_results
import match_finds
import remfits
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

parsearg = argparse.ArgumentParser(description='Match locations of objects within image and find object results', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', nargs=1, type=str, help='Prefix part of location, find results and image file')
remdefaults.parseargs(parsearg, tempdir=False, inlib=False)
parsearg.add_argument('--imagefile', type=str, help='Image file in case different from files argument')
parsearg.add_argument('--findres', type=str, help='Find results file in case different from files argument')
parsearg.add_argument('--objloc', type=str, help='Object location file in case different from files argument')
parsearg.add_argument('--threshold', type=float, default=20.0, help='Threshold for match in arcsec')
parsearg.add_argument('--verbose', action='store_true', help='Give statistics')
parsearg.add_argument('--idonly', action='store_true', help='Just keep things that have been identified')
parsearg.add_argument('--usonly', action='store_true', help='Just keep things that are usable')
parsearg.add_argument('--shiftmax', type=int, default=4, help='Maxmimum shift of centre when repositioning')

resargs = vars(parsearg.parse_args())
prefix = resargs['files'][0]
remdefaults.getargs(resargs)
threshold = resargs['threshold']
verbose = resargs['verbose']
idonly = resargs['idonly']
usonly = resargs['usonly']
imagefile = resargs['imagefile']
findresfile = resargs['findres']
locfile = resargs['objloc']
maxshift = resargs['shiftmax']

if imagefile is None:
    imagefile = prefix
if findresfile is None:
    findresfile = prefix
if locfile is None:
    locfile = prefix

try:
    inputfile = remfits.parse_filearg(imagefile, None)
except remfits.RemFitsErr as e:
    print(e.args[0], file=sys.stderr)
    sys.exit(52)

locations = obj_locations.load_objlist_from_file(locfile, inputfile)
findres = find_results.load_results_from_file(findresfile, inputfile)

try:
    matchlist = match_finds.allocate_locs(locations, findres, threshold)
except match_finds.FindError as e:
    print("Match of", findresfile, "gave error", e.args[0], file=sys.stderr)
    sys.exit(200)

locr = locations.resultlist
findr = findres.resultlist

hadt = 0

for row, col, dist in matchlist:
    f = findr[col]
    l = locr[row]
    f.obj = l
    f.istarget = l.istarget
    if f.istarget:
        hadt += 1
    if l.objinfo.apsize not in (0, f.apsize):
        f.needs_correction = True
        f.apsize = l.objinfo.apsize

if hadt == 0:
    print("Did not find a target", file=sys.stderr)
    sys.exit(240)

if idonly or usonly:
    noid = nouse = 0
    newf = []
    for fr in findr:
        if idonly:
            if  fr.obj is None:
                noid += 1
            elif not fr.obj.usable:
                nouse += 1
            else:
                newf.append(fr)
        else:
            newf.append(fr)
    if nouse + noid > 0:
        findres.resultlist = newf
        findres.rekey()
        if verbose:
            if nouse > 0:
                print(nouse, "not usable eliminated", file=sys.stderr)
            if noid > 0:
                print(noid, "not identified eliminated", file=sys.stderr)

for f in findres.results():
    if not f.needs_correction:
        continue
    f.col, f.row, f.adus, newpixc = findres.findbest_colrow(f.col, f.row, f.apsize, maxshift)
    f.needs_correction = False

findres.reorder()
findres.relabel()
find_results.save_results_to_file(findres, findresfile, True)

if findres.num_results() < 2:
    if findres.num_results(True) == 1:
        print("No results in file other than target", file=sys.stderr)
        sys.exit(241)
    print("No results in file", file=sys.stderr)
    sys.exit(242)

if verbose:
    n = nfound = 0
    for f in findres.results():
        n += 1
        if len(f.name) != 0:
            nfound += 1
    print(nfound, "found out of", n, file=sys.stderr)
