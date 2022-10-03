#!  /usr/bin/env python3

"""Suppress objects we have hidden"""

import argparse
import sys
import remdefaults
import find_results

parsearg = argparse.ArgumentParser(description='Apply edits created by display image to single result', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', nargs='+', type=str, help='Findres files')
remdefaults.parseargs(parsearg, tempdir=False, inlib=False)
parsearg.add_argument('--verbose', action='store_true', help='Tell everything')

resargs = vars(parsearg.parse_args())
files = resargs['files']
verbose = resargs['verbose']

mydb, dbcurs = remdefaults.opendb()

objinds = set()
dbchanges = errors = 0

for file in files:
    try:
        findres = find_results.load_results_from_file(file)
    except find_results.FindResultErr as e:
        print("Cannot open", file, "error was", e.args[0], file=sys.stderr)
        errors += 1
        continue
    for fr in findres.results(idonly=True):
        if fr.hide:
            objinds.add(fr.obj.objind)

if errors != 0:
    print("Halting as", errors, "errors found", file=sys.stderr)
    sys.exit(10)

if len(objinds) == 0:
    if verbose:
        print("No changes to be made", file=sys.stderr)
    sys.exit(1)

for ind in objinds:
    dbc = dbcurs.execute("UPDATE objdata SET suppress=1,label=NULL WHERE ind={:d}".format(ind))
    dbchanges += dbc
    if verbose:
        if dbc != 0:
            print("Updated", ind, file=sys.stderr)
        else:
            print("No changes made to", ind, file=sys.stderr)

if dbchanges == 0:
    if verbose:
        print("No changes made", file=sys.stderr)
    sys.exit(1)
mydb.commit()
if verbose:
    print(dbchanges, "changes made", file=sys.stderr)
