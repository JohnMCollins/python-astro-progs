#!  /usr/bin/env python3

"""Reset aperture size of object in database"""

import argparse
import sys
import remdefaults
import objdata

parsearg = argparse.ArgumentParser(description='Set aperture size in DB', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('object', nargs='+', type=str, help='Object name(s)')
parsearg.add_argument('--apsize', type=int, required=True, help='Aperture size to set')
remdefaults.parseargs(parsearg, tempdir=False, libdir=False)

resargs = vars(parsearg.parse_args())
targobjs = resargs['object']
remdefaults.getargs(resargs)
apsize = resargs['apsize']
mydb, mycurs = remdefaults.opendb()

updates = 0

for targobj in targobjs:

    tobj = objdata.ObjData(targobj)

    try:
        tobj.get(mycurs)
    except objdata.ObjDataError as e:
        print("Cannot find", targobj, e.args[0], file=sys.stderr)
        continue

    if tobj.apsize == apsize:
        continue

    tobj.apsize = apsize
    tobj.update(mycurs)
    updates += 1

if updates != 0:
    mydb.commit()
    print(updates, "object(s) update")
    sys.exit(0)

print("No objects updated")
sys.exit(1)
