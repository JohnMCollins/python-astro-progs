#!  /usr/bin/env python3

"""Hide objects in findres files which are variable"""

import argparse
import sys
import remdefaults
import find_results

# Keep trck of all objects we've looked at and the ones which are variable

allobj_cache = dict()


def is_variable(ind):
    """Return True if object selected by ind is variable, updating caches"""
    try:
        return  allobj_cache[ind]
    except KeyError:
        pass
    mycursor.execute("SELECT variability FROM objdata WHERE ind={:d}".format(ind))
    res = mycursor.fetchone()
    allobj_cache[ind] = res is not None and res[0] is not None
    return allobj_cache[ind]


parsearg = argparse.ArgumentParser(description='Hide variable objects in findres files', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', nargs='+', type=str, help='Findres files')
parsearg.add_argument('--verbose', action='count', help="Be increasingly verbose")
remdefaults.parseargs(parsearg, tempdir=False, database=False)

resargs = vars(parsearg.parse_args())
files = resargs['files']
verbose = resargs['verbose']
remdefaults.getargs(resargs)

mydb, mycursor = remdefaults.opendb()

errors = 0

for file in files:

    try:
        findres = find_results.load_results_from_file(file)
    except find_results.FindResultErr as e:
        print(file, "Gave error", e.args[0], file=sys.stderr)
        errors += 1
        continue

    frchanges = 0

    for fr in findres.results(idonly=True, nohidden=True):
        if is_variable(fr.obj.objind):
            fr.hide = True
            frchanges += 1
            if verbose > 1:
                print("Setting", fr.obj.dispname, "to hidden in", file, file=sys.stderr)

    if  frchanges != 0:
        if verbose > 0:
            print("Saving", file, "wtih", frchanges, "changes", file=sys.stderr)
        try:
            find_results.save_results_to_file(findres, file, force=True)
        except find_results.FindResultErr as e:
            print("Saving", file, "gave error", e.args[0], file=sys.stderr)
            errors += 1

if errors > 0:
    sys.exit(1)
