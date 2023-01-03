#!  /usr/bin/env python3

"""Set variability of objects by label"""

import argparse
import sys
import remdefaults

parsearg = argparse.ArgumentParser(description='Set variability of objects by label', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('objects', nargs='+', type=str, help='Labels of objects')
parsearg.add_argument('--vicinity', type=str, choices=['GJ551', 'GJ699', 'GJ729'], required=True, help='Select vicinity of objects')
parsearg.add_argument('--variability', type=float, default=0.0, help='Variability to set')
remdefaults.parseargs(parsearg, tempdir=False)

resargs = vars(parsearg.parse_args())
objects = set(resargs['objects'])
vicinity = resargs['vicinity']
remdefaults.getargs(resargs)
var = resargs['variability']

mydb, mycurs = remdefaults.opendb()
objesc = [mydb.escape(obj) for obj in objects]
mycurs.execute("SELECT label FROM objdata WHERE vicinity=%s AND label IN (" + ",".join(objesc) + ")", vicinity)
lrows = mycurs.fetchall()

if len(lrows) == 0:
    print("Did not find any objects", file=sys.stderr)
    sys.exit(10)

if len(lrows) != len(objects):
    print("Warning did not find", file=sys.stderr)
    readobjs = { r[0] for r in lrows }
    print(", ".join(sorted(objects-readobjs)), file=sys.stderr)

ret = mycurs.execute(("UPDATE objdata SET variability={:.8e} WHERE vicinity=%s AND label IN (" + ",".join(objesc) + ")").format(var), vicinity)

if ret == 0:
    print("Nothing got updated", file=sys.stderr)
    sys.exit(1)

print(ret, "updated", file=sys.stderr)
mydb.commit()
