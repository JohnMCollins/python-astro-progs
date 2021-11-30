#!  /usr/bin/env python3

"""Diesplay find result with all of specified objects in"""

import argparse
import sys
import os
import glob
import remdefaults
import objdata
import find_results
import miscutils

parsearg = argparse.ArgumentParser(description='Display find results with all of given objects in', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('objects', type=str, nargs='+', help='Objects to look for')
remdefaults.parseargs(parsearg, tempdir=False, inlib=False)
parsearg.add_argument('--directory', type=str, help='Directory if not current')
parsearg.add_argument('--filter', type=str, help='Filter to use')

resargs = vars(parsearg.parse_args())
objects = resargs['objects']
remdefaults.getargs(resargs)
direc = resargs['directory']
filt = resargs['filter']

if direc:
    os.chdir(direc)

db, mycurs = remdefaults.opendb()

objstr_set = set()
errors = 0

for obj in objects:

    try:
        objstr_set.add(objdata.get_objname(mycurs, obj, allobj=True))
    except objdata.ObjDataError as e:
        print("Cannot find", obj, "error was", e.args[0], e.args[1], file=sys.stderr)
        errors += 1
        continue

if errors > 0 or len(objstr_set) == 0:
    print("Aborting due to errors", file=sys.stderr)
    sys.exit(10)

resultfiles = set()

for file in glob.iglob('*.findres'):

    try:
        findres = find_results.load_results_from_file(file)
    except find_results.FindResultErr:
        continue

    if filt and filt != findres.filter:
        continue

    try:
        for obj in objstr_set:
            n = findres[obj]
    except find_results.FindResultErr:
        continue

    resultfiles.add(miscutils.removesuffix(file, 'findres'))

for rf in sorted(resultfiles):
    print(rf)
