#!  /usr/bin/env python3

"""Display findresult file"""

import argparse
import sys
import warnings
from astropy.utils.exceptions import ErfaWarning
import remdefaults
import find_results
import col_from_file

warnings.simplefilter('ignore', ErfaWarning)

parsearg = argparse.ArgumentParser(description='Create findres files from database', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('ids', nargs='*', type=str, help='Obs ids to convert or stdin')
remdefaults.parseargs(parsearg, tempdir=False, inlib=False)
parsearg.add_argument('--prefix', type=str, default='frout', help='Prefix of output files')
parsearg.add_argument('--colnum', type=int, default=0, help='Column to use from stdin')
parsearg.add_argument('--force', action='store_true', help='Force if file exists')

resargs = vars(parsearg.parse_args())
ids = resargs['ids']
remdefaults.getargs(resargs)
prefix = resargs['prefix']
force = resargs['force']
if len(ids) == 0:
    ids = col_from_file.col_from_file(sys.stdin, resargs['colnum'])

errors = 0

mydb, dbcurs = remdefaults.opendb()

for idstr in ids:
    try:
        intid = int(idstr)
    except ValueError:
        print(idstr, "is an invalid obsid", file=sys.stderr)
        errors += 1
        continue

    findres = find_results.FindResults()
    try:
        findres.loaddb(dbcurs)
    except find_results.FindResultErr as e:
        print(e.args[0], file=sys.stderr)
        errors += 1
        continue

    try:
        find_results.save_results_to_file(findres, prefix + idstr, force=force)
    except find_results.FindResultErr as e:
        print("Could not save results for", idstr, "error was", e.args[0], file=sys.stderr)
        errors += 1

if errors != 0:
    print(errors, "erroneous ids out of", len(ids), file=sys.stderr)
    sys.exit(1)
sys.exit(0)
