#!  /usr/bin/env python3

"""Reset apperture size of object or suppress"""

import argparse
import sys
import remdefaults
import objdata

parsearg = argparse.ArgumentParser(description='Reset aperture size of object or suppress', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('obj', nargs='+', type=str, help='Object or objects')
parsearg.add_argument('--apsize', type=int, help='Aperture to set')
parsearg.add_argument('--supp', action='store_true', help='Set to suppress')
parsearg.add_argument('--nosupp', action='store_true', help='Set to not suppress')
parsearg.add_argument('--verbose', action='store_true', help='Give blow-by-blow account')
remdefaults.parseargs(parsearg, tempdir=False)

resargs = vars(parsearg.parse_args())
objects = resargs['obj']
apsize = resargs['apsize']
supp = resargs['supp']
nosupp = resargs['nosupp']
verbose = resargs['verbose']
remdefaults.getargs(resargs)

if supp and nosupp:
    print("Cannot have both --supp and ---nosupp", file=sys.stderr)
    sys.exit(10)

if not supp and not nosupp and apsize is None:
    print("Not doing anything", file=sys.stderr)
    sys.exit(10)

mydb, dbcurs = remdefaults.opendb()

changes = 0

fupd = []
if supp:
    fupd.append("suppress=1")
if nosupp:
    fupd.append("suppress=0")
if apsize is not None:
    fupd.append("apsize=%d" % apsize)

for obj in objects:
    mainname = objdata.get_objname(dbcurs, obj, allobj=True)
    n = dbcurs.execute("UPDATE objdata SET " + ",".join(fupd) + " WHERE objname=%s", mainname)
    if verbose:
        if n != 0:
            print(mainname, "was changed", file=sys.stderr)
        else:
            print(mainname, "was not changed", file=sys.stderr)
    changes += n

if changes != 0:
    mydb.commit()
    if verbose:
        print(changes, "changes", file=sys.stderr)
    sys.exit(0)
if verbose:
    print("No changes", file=sys.stderr)
sys.exit(1)
