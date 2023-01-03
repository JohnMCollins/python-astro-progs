#!  /usr/bin/env python3

"""Display findresult file"""

import argparse
import sys
import warnings
from astropy.utils.exceptions import ErfaWarning
import remdefaults
import find_results

warnings.simplefilter('ignore', ErfaWarning)

parsearg = argparse.ArgumentParser(description='Convert findres files to database', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', nargs='+', type=str, help='Find results file(s)')
remdefaults.parseargs(parsearg, tempdir=False, inlib=False)
parsearg.add_argument('--remove', action='store_false', help='Remove existing records with same object and obs')

resargs = vars(parsearg.parse_args())
files = resargs['files']
remdefaults.getargs(resargs)
remove = resargs['remove']

errors = 0
mydb, dbcurs = remdefaults.opendb()

for fil in files:
    try:
        findres = find_results.load_results_from_file(fil)
    except find_results.FindResultErr as e:
        print(fil, "gave error", e.args[0], file=sys.stderr)
        errors += 1
        continue
    if findres.num_results(idonly=True) == 0:
        print(fil, "Has no identified objects in it", file=sys.stderr)
        errors += 1
        continue
    if findres.obsind is None:
        print(fil, "has no obsind", file=sys.stderr)
        errors += 1
        continue
    dbcurs.execute("SELECT rejreason FROM obsinf WHERE obsind={:d}".format(findres.obsind))
    ns = dbcurs.fetchall()
    if len(ns) != 1:
        print(fil, "refers to unknown obsind {:d}".format(findres.obsind), file=sys.stderr)
        errors += 1
        continue
    if ns[0][0] is not None:
        print(fil, "Refers to rejected obs {:d} for reason {:s}".format(findres.obsind, ns[0][0]))
        errors += 1
        continue

    findres.savedb(dbcurs, remove)

if errors != 0:
    print(errors, "erroneous files out of", len(files), file=sys.stderr)
    sys.exit(1)
sys.exit(0)
