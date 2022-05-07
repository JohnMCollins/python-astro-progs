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
frfields = "INSERT INTO findresult (obsind,objind,nrow,ncol,rdiff,cdiff,radeg,decdeg,apsize,adus,hide) VALUES ({:s})"

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

    rerrs = 0

    # Run through and check before fiddling

    for fr in findres.results(idonly=True):
        dbcurs.execute("SELECT COUNT(*) FROM objdata WHERE ind={:d}".format(fr.obj.objind))
        ns = dbcurs.fetchall()
        if ns[0][0] != 1:
            print(fil, "refers to objid {:d} which could not be found".format(fr.obj.objind))
            rerrs += 1

    if rerrs > 0:
        print(fil, "has", rerrs, "errros in results", file=sys.stderr)
        errors += 1
        continue

    if remove:
        dbcurs.execute("DELETE FROM findresult WHERE obsind={:d}".format(findres.obsind))

    for fr in findres.results(idonly=True):
        fvalues = []
        fvalues.append("{:d}".format(findres.obsind))
        fvalues.append("{:d}".format(fr.obj.objind))
        fvalues.append("{:d}".format(fr.row))
        fvalues.append("{:d}".format(fr.col))
        fvalues.append("{:d}".format(fr.rdiff))
        fvalues.append("{:d}".format(fr.cdiff))
        fvalues.append("{:.8e}".format(fr.radeg))
        fvalues.append("{:.8e}".format(fr.decdeg))
        fvalues.append("{:.4g}".format(fr.apsize))
        fvalues.append("{:.8e}".format(fr.adus))
        fvalues.append(str(fr.hide))
        dbcurs.execute(frfields.format(','.join(fvalues)))

    mydb.commit()

if errors != 0:
    print(errors, "erroneous files out of", len(files), file=sys.stderr)
    sys.exit(1)
sys.exit(0)
