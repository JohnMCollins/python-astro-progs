#! /usr/bin/env python3

"""Delete FITS files we don't care about"""

import argparse
import sys
import remdefaults
import remtargets

parsearg = argparse.ArgumentParser(description='Run through database and delete FITS files which are not of targets', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg, libdir=False, tempdir=False)
parsearg.add_argument('--savenumb', type=int, default=100, help='Commit after this number of deletions')
parsearg.add_argument("--debug", action='store_true', help='Debug selection statement')
resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
debug = resargs['debug']
savenumb = resargs['savenumb']
if savenumb < 1:
    savenumb = 1

mydb, dbcurs = remdefaults.opendb()

targselect = []
remtargets.remtargets(dbcurs, targselect)

selection = "SELECT obsind,ind,object FROM obsinf WHERE ind!=0 AND NOT (" + " OR ".join(targselect) + ")"
if debug:
    print("Selection:", selection, file=sys.stderr)

dbcurs.execute(selection)
indsrows = dbcurs.fetchall()
n = 0

dhash = dict()

for obsind, ind, targ in indsrows:
    dbcurs.execute("UPDATE obsinf SET ind=0 WHERE obsind={:d}".format(obsind))
    dbcurs.execute("DELETE FROM fitsfile WHERE ind={:d}".format(ind))
    n += 1
    if n % savenumb == 0:
        mydb.commit()
    try:
        dhash[targ] += 1
    except KeyError:
        dhash[targ] = 1

mydb.commit()

for k in sorted(dhash.keys()):
    print(k, dhash[k])
