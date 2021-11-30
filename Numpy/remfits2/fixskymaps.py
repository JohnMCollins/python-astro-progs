#!  /usr/bin/env python3

"""Fix sky map files after updating object aperture or suppress flag"""

import argparse
import sys
import remdefaults
import objdata

parsearg = argparse.ArgumentParser(description='Fix sky map files after updating aperture or suppress flag', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('objects', type=str, nargs='+', help='Objects to adjust')
remdefaults.parseargs(parsearg, tempdir=False, inlib=False)

resargs = vars(parsearg.parse_args())
objects = resargs['objects']
remdefaults.getargs(resargs)

db, mycurs = remdefaults.opendb()

obstr_list = dict()
errors = 0
vicinities = set()

for obj in objects:

    try:
        objstr = objdata.ObjData(obj)
        objstr.get(mycurs, allobj=True)
    except objdata.ObjDataError as e:
        print("Cannot find", obj, "error was", e.args[0], e.args[1], file=sys.stderr)
        errors += 1
        continue
    obstr_list[objstr.objname] = objstr
    vicinities.add(objstr.vicinity)

if errors > 0 or len(obstr_list) == 0:
    print("Aborting due to errors", file=sys.stderr)
    sys.exit(10)

for vic in vicinities:

    for sk in remdefaults.skymap_glob(vic):

        changes = 0
        dlist = []
        skm = objdata.load_cached_objs_from_file(sk)
        for n, cobj in enumerate(skm.objlist):
            try:
                dbobj = obstr_list[cobj.objname]
            except KeyError:
                continue
            if dbobj.suppress:
                dlist.append(n)
                changes += 1
            if dbobj.apsize != cobj.apsize:
                cobj.apsize = dbobj.apsize
                changes += 1
        for d in reversed(dlist):
            skm.objlist.pop(d)
        if changes != 0:
            objdata.save_cached_objs_to_file(skm, sk)
