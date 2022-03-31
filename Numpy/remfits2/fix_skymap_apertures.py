#!  /usr/bin/env python3

"""Fix apertures in skymap files"""

import argparse
import sys
import os
import glob
import remdefaults
import objdata

parsearg = argparse.ArgumentParser(description='Fix apertures in skymap files to save regen', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', nargs='*', help='Files to look at otherwise all skymap files in directory')
remdefaults.parseargs(parsearg, tempdir=False, inlib=False)
parsearg.add_argument('--directory', type=str, help='Directory if not current')

resargs = vars(parsearg.parse_args())
files = resargs['files']
remdefaults.getargs(resargs)
direc = resargs['directory']

if direc:
    os.chdir(direc)

if len(files) == 0:
    files = glob.glob('*.skymap')
    if len(files) == 0:
        print("No files to work on", file=sys.stderr)
        sys.exit(10)

db, mycurs = remdefaults.opendb()

fileschanged = 0
errors = 0

aps = dict()
iraps = dict()

for file in files:

    try:
        olist = objdata.load_cached_objs_from_file(file)
    except objdata.ObjDataError as e:
        print("Error", e.args[0], "Loading", file, file=sys.stderr)
        errors += 1
        continue

    apchanges = 0
    for obj in olist.objlist:
        try:
            ap = aps[obj.objind]
            irap = iraps[obj.objind]
        except KeyError:
            mycurs.execute("SELECT apsize,irapsize FROM objdata WHERE ind={:d}".format(obj.objind))
            r = mycurs.fetchall()
            if len(r) != 1:
                print("Error cannot find objind", obj.objind, "name", obj.dispname, file=sys.stderr)
                errors += 1
                continue
            ap, irap = r[0]
            aps[obj.objind] = ap
            iraps[obj.objind] = irap

        if obj.apsize != ap or obj.irapsize != irap:
            obj.apsize = ap
            obj.irapsize = irap
            apchanges += 1

    if apchanges != 0:
        try:
            objdata.save_cached_objs_to_file(olist, file)
            fileschanged += 1
        except objdata.ObjDataError as e:
            print("Error cannot save changed", file, e.args[0], file=sys.stderr)

print(fileschanged, "files changed", file=sys.stderr)
if errors != 0:
    print(errors, "Errors", file=sys.stderr)
    sys.exit(1)
sys.exit(0)
