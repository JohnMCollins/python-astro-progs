#!  /usr/bin/env python3

"""Mark observation as unacceptable for given reason"""

import argparse
import sys
import remdefaults

parsearg = argparse.ArgumentParser(description='Mark observations rejected', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('obs', nargs='+', type=int, help='Observation id(s)')
remdefaults.parseargs(parsearg, tempdir=False, inlib=False)
parsearg.add_argument('--delfits', action='store_true', help='Delete FITS file if present')
parsearg.add_argument('--reason', type=str, nargs='+', required=True, help='Reason description spaces not required, term by --')
parsearg.add_argument('--override', action='store_true', help='Override existing reason if present')

resargs = vars(parsearg.parse_args())
files = set(resargs['obs'])
remdefaults.getargs(resargs)
delfits = resargs['delfits']
reason = ' '.join(resargs['reason'])
override = resargs['override']

if len(reason) == 0:
    print("Cannot have empty reason", file=sys.stderr)
    sys.exit(10)

mydb, dbcurs = remdefaults.opendb()

orcl = []
for oind in files:
    orcl.append("obsind=%d" % oind)
orcl = " OR ".join(orcl)
dbcurs.execute("SELECT obsind,ind,rejreason FROM obsinf WHERE " + orcl)
errors = 0
inds = []
for oind, ind, sreason in dbcurs.fetchall():
    if not override and sreason and sreason != reason:
        print(oind, "has already got reason", sreason, "user --override if needed", file=sys.stderr)
        errors += 1
    if ind != 0:
        inds.append(ind)
if errors != 0:
    print("Quitting due to errors", file=sys.stderr)
    sys.exit(11)

if delfits:
    dbcurs.execute("UPDATE obsinf SET rejreason=%s,ind=0 WHERE " + orcl, reason)
    if len(inds) != 0:
        inds = set(inds)
        iorcl = []
        for ind in inds:
            iorcl.append("ind=%d" % ind)
        dbcurs.execute("DELETE FROM fitsfile WHERE " + " OR ".join(iorcl))
else:
    dbcurs.execute("UPDATE obsinf SET rejreason=%s WHERE " + orcl, reason)

mydb.commit()
