#!  /usr/bin/env python3

"""Set suppress marker on objects overlapping given targets and file skymap, objloc and findres files"""

import argparse
import sys
import os
import glob
import remdefaults
import objdata
import find_results
import obj_locations
import miscutils

parsearg = argparse.ArgumentParser(description='Set suppress marker on objects overlapping given objects', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('objects', type=str, nargs='+', help='Objects to deal with overlapping objects')
remdefaults.parseargs(parsearg, tempdir=False, inlib=False)
parsearg.add_argument('--directory', type=str, help='Directory if not current')
parsearg.add_argument('--shiftmax', type=int, default=10, help='Maxmimum shift of centre')
parsearg.add_argument('--filter', type=str, help='Restrict to files with given filter')

resargs = vars(parsearg.parse_args())
objects = resargs['objects']
remdefaults.getargs(resargs)
direc = resargs['directory']
shiftmax = resargs['shiftmax']
filt = resargs['filter']

if direc:
    os.chdir(direc)

vicinities = set()
namelist = set()

db, mycurs = remdefaults.opendb()
for nam in objects:
    try:
        objd = objdata.ObjData(nam)
        objd.get(mycurs, allobj=True)  # In case we half-did it before, include already suppressed
        namelist.add(objd.objname)
        vicinities.add(objd.vicinity)
    except objdata.ObjDataError:
        continue

frlist = set()
supplist = set()

for frfile in glob.iglob('*.findres'):
    findres = find_results.load_results_from_file(frfile)
    if filt and filt != findres.filter:
        continue
    clashlist = findres.overlap_check()
    if len(clashlist) == 0:
        continue
    changes = 0
    for first, second in clashlist:
        firstname = findres[first].name
        secondname = findres[second].name
        if len(firstname) == 0 or len(secondname) == 0:
            continue
        if firstname in namelist:
            supplist.add(secondname)
            changes += 1
        elif secondname in namelist:
            supplist.add(firstname)
            changes += 1
    if changes > 0:
        frlist.add(miscutils.removesuffix(frfile, 'findres'))

if len(supplist) == 0:
    print("Do not need to do anything", file=sys.stderr)
    sys.exit(1)

dups = namelist & supplist
if len(dups) != 0:
    print("Common names", ",".join(sorted(dups)), "in names and suppress lists", file=sys.stderr)
    sys.exit(10)

# Now set suppress in DB

mycurs.execute("UPDATE objdata SET suppress=1 WHERE " + " OR ".join(["objname=" + db.escape(s) for s in supplist]))
db.commit()

# Now fix skymap files

for vic in vicinities:
    for sk in remdefaults.skymap_glob(vic):
        changes = 0
        dlist = []
        skm = objdata.load_cached_objs_from_file(sk)
        for n, cobj in enumerate(skm.objlist):
            if cobj.objname in supplist:
                dlist.append(n)
                changes += 1
        while len(dlist) != 0:
            skm.objlist.pop(dlist.pop())
        if changes != 0:
            objdata.save_cached_objs_to_file(skm, sk)

# Fix objloc files
# Have to do all of them

for file in glob.iglob('*.objloc'):

    olocf = obj_locations.load_objlist_from_file(file)
    changes = 0
    dlist = []
    for n, cobj in enumerate(olocf.results()):
        if cobj.name in supplist:
            dlist.append(n)
            changes += 1
    while len(dlist) != 0:
        olocf.resultlist.pop(dlist.pop())
    if changes != 0:
        obj_locations.save_objlist_to_file(olocf, file, force=True)

# Better do all findres files as objects might be in any of them but we don't need
# to worry about the fits files.

for file in glob.iglob('*.findres'):
    try:
        findres = find_results.load_results_from_file(file)
    except find_results.FindResultErr:
        continue

    # dlist = [] not needed as we popped everything above
    changes = 0
    for n, fr in enumerate(findres.results()):
        if fr.name in supplist:
            dlist.append(n)
            changes += 1
    while len(dlist) != 0:
        findres.resultlist.pop(dlist.pop())
    if changes != 0:
        findres.reorder()
        findres.relabel()
        find_results.save_results_to_file(findres, file, force=True)
