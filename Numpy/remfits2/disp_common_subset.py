#!  /usr/bin/env python3

"""Display overlaps in find results"""

import argparse
import sys
import numpy as np
import remdefaults
import find_results
import objdata

parsearg = argparse.ArgumentParser(description='Display common subsets of objects in find results', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', nargs='+', type=str, help='Find results files')
remdefaults.parseargs(parsearg, tempdir=False, inlib=False)
parsearg.add_argument('--target', type=str, required=True, help='Target to restrict to')
parsearg.add_argument('--filter', type=str, help='Filter name to restrict to')
parsearg.add_argument('--autohide', action='store_true', help='Auto-hide overlapping results')
parsearg.add_argument('--byrc', action='store_true', help='Sort by row then column other than descending brightness')

resargs = vars(parsearg.parse_args())
files = resargs['files']
remdefaults.getargs(resargs)
target = resargs['target']
filt = resargs['filter']
byrc = resargs['byrc']
autohide = resargs['autohide']

nfiles = 0

ndict = dict()

for fil in files:
    try:
        findres = find_results.load_results_from_file(fil)
    except find_results.FindResultErr as e:
        print(fil, "gave error", e.args[0], file=sys.stderr)
        continue
    if findres.num_results(idonly=True, nohidden=True) == 0:
        print(fil, "has no results", file=sys.stderr)
        continue
    targfr = findres[0]
    if not targfr.istarget or targfr.hide:
        print(fil, "has no target", file=sys.stderr)
        continue
    if targfr.obj.objname != target:
        continue
    if filt and filt != findres.filter:
        continue

    for fr in findres.results(idonly=True, nohidden=True):
        try:
            ndict[fr.obj.dispname] += 1
        except KeyError:
            ndict[fr.obj.dispname] = 1
    nfiles += 1

print("Number of files:", nfiles)
for f in sorted(ndict.keys()):
    if ndict[f] == nfiles:
        print(f, ndict[f], sep='\t')
