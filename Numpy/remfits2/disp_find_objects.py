#!  /usr/bin/env python3

"""Display findresult file"""

import argparse
import warnings
import sys
import remdefaults
import obj_locations
import find_results
import match_finds
import objdata

from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)

parsearg = argparse.ArgumentParser(description='Display found objects in find results', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', nargs='+', type=str, help='Find results files')
remdefaults.parseargs(parsearg, tempdir=False, inlib=False)
parsearg.add_argument('--lower', type=int, default=1, help='Lower limit of occurrences to display')

resargs = vars(parsearg.parse_args())
files = resargs['files']
remdefaults.getargs(resargs)
lowerlim = resargs['lower']

foundcount = dict()

for fil in files:
    try:
        findres = find_results.load_results_from_file(fil)
    except find_results.FindResultErr as e:
        print(fil, "gave error", e.args[0], file=sys.stderr)
        continue
    for r in findres.results():
        try:
            foundcount[r.name] += 1
        except KeyError:
            foundcount[r.name] = 1

rtab = [(n, c) for n, c in foundcount.items()]
rtab.sort(key=lambda x: x[1], reverse=True)
nwidth = max([len(x[0]) for x in rtab])
for n, c in rtab:
    if c < lowerlim:
        break
    print("{n:<{wid}s} {c:4d}".format(wid=nwidth, n=n, c=c))
