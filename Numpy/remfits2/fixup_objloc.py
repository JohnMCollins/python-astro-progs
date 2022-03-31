#!  /usr/bin/env python3

"""Sort object locations by distance order"""

import argparse
import sys
import objdata
import obj_locations
import remdefaults

parsearg = argparse.ArgumentParser(description='Go through objlec files and adjust apertures', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', nargs='+', type=str, help='Objloc files')
remdefaults.parseargs(parsearg, tempdir=False, inlib=False, database=False)

resargs = vars(parsearg.parse_args())
flist = resargs['files']
remdefaults.getargs(resargs)

mydb, dbcurs = remdefaults.opendb()

errors = 0

apsizes = dict()

for ofile in flist:
    try:
        olocfl = obj_locations.load_objlist_from_file(ofile, None)
    except obj_locations.ObjLocErr as e:
        print(ofile, "gave error on open", e.args[0], file=sys.stderr)
        errors += 1
        continue
    adjs = 0
    for ol in olocfl.results():
        if ol.apsize == 0:
            try:
                ol.apsize = apsizes[ol.objind]
                if ol.apsize != 0:
                    adjs += 1
                continue
            except KeyError:
                pass
            if ol.objind == 0:
                print("Zeor objind in objloc for", ol.dispname, file=sys.stderr)
                errors += 1
            nod = objdata.ObjData()
            try:
                nod.get(dbcurs, ind=ol.objind)
            except objdata.ObjDataError as e:
                print("Problems getting apsize for", ol.dispname, e.args[0], file=sys.stderr)
                errors += 1
                continue
            apsizes[ol.objind] = nod.apsize
            if nod.apsize != 0:
                ol.apsize = nod.apsize
                adjs += 1
    if adjs > 0:
        try:
            obj_locations.save_objlist_to_file(olocfl, ofile, force=True)
        except obj_locations.ObjLocErr as e:
            print(ofile, "gave error on save", e.args[0], file=sys.stderr)
            errors += 1

if errors > 0:
    sys.exit(1)
sys.exit(0)
