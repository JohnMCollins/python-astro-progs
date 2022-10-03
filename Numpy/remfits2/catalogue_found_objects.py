#!  /usr/bin/env python3

"""Catalogue objects in a collection of findres files and list number/mean std"""

import argparse
import sys
import math
import remdefaults
import find_results


class foundobject:
    """Class for recording details of object"""

    def __init__(self, fres):
        self.count = 1
        self.name = fres.obj.objname
        self.objind = fres.obj.objind
        self.objtype = fres.obj.objtype
        self.adus = fres.adus
        self.adusq = fres.adus**2
        self.label = ""
        self.mean = self.std = None
        if fres.obj.valid_label():
            self.label = fres.obj.label

Obj_dict = dict()

parsearg = argparse.ArgumentParser(description='Catalgoue found object results', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', nargs='+', type=str, help='Find results file(s)')
parsearg.add_argument('--filter', type=str, default='griz', help='Filters to restrict to')
parsearg.add_argument('--minlimit', type=int, default=5, help='Ignore objects with occurences less than this')
parsearg.add_argument('--update', action='store_true', help='Update labels in database')
remdefaults.parseargs(parsearg, tempdir=False, inlib=False)

resargs = vars(parsearg.parse_args())
files = resargs['files']
filtlim = resargs['filter']
occlim = resargs['minlimit']
update = resargs['update']
remdefaults.getargs(resargs)

# Get stuff from DB rather than file

mydb, mycu = remdefaults.opendb()

errors = 0
vicinity = None

for fil in files:
    try:
        findres = find_results.load_results_from_file(fil)
    except find_results.FindResultErr as e:
        print(fil, "gave error", e.args[0], file=sys.stderr)
        errors += 1
        continue
    if findres.filter not in filtlim:
        continue
    for fr in findres.results(idonly=True, nohidden=True):
        if vicinity is None:
            vicinity = fr.obj.vicinity
        elif vicinity != fr.obj.vicinity:
            print("Unexpected vicinity", fr.obj.vicinity, "for object", fr.obj.dispname, "expecting", vicinity, file=sys.stderr)
            errors +=1
            break
        if fr.obj.objind in Obj_dict:
            fo = Obj_dict[fr.obj.objind]
            fo.count += 1
            fo.adus += fr.adus
            fo.adusq += fr.adus**2
        else:
            fo = foundobject(fr)
            mycu.execute("SELECT label FROM objdata WHERE ind={:d}".format(fo.objind))
            rw = mycu.fetchone()
            if rw is None:
                print("Cannot find object {:s} id {:d}".format(fo.name, fo.objind), file=sys.stderr)
                errors += 1
                continue
            fo.label = rw[0]
            if fo.label is None:
                fo.label = ""
            Obj_dict[fr.obj.objind] = fo

if errors > 0:
    print("Stopping due to", errors, "errors", file=sys.stderr)

folist = [fo for fo in Obj_dict.values() if fo.count >= occlim]
for fo in folist:
    fo.mean = fo.adus / fo.count
    fo.std = math.sqrt(fo.adusq / fo.count - fo.mean**2)

folist = sorted(sorted(folist, key=lambda x: - x.mean), key=lambda x: - x.count)
nlength = max([len(fo.name) for fo in folist])
try:
    for fo in folist:
        print("{nam:<{nlength}s} {lab:<3s} {mn:10.2f} {st:10.2f} {pc:7.2f} {cnt:3d} {typ:s}".format(nam=fo.name, nlength=nlength, \
                                                                                            typ=fo.objtype, lab=fo.label, mn=fo.mean, st=fo.std,
                                                                                            pc=fo.std*100.0/fo.mean, cnt=fo.count))
except (KeyboardInterrupt, BrokenPipeError):
    sys.exit(0)

if not update:
    sys.exit(0)

if folist[0].name != vicinity:
    print("Top of list ({:s} does not seem to be same as target of {:s}".format(folist[0].name, vicinity), file=sys.stderr)
    sys.exit(200)

base = ord('A')
for n, fo in enumerate(folist):
    l = chr(base + n % 26)
    if n >= 26:
        l += str(n // 26)
    fo.label = l

try:
    print("After relabel....")
    for fo in folist:
        print("{nam:<{nlength}s} {lab:<3s} {mn:10.2f} {st:10.2f} {pc:7.2f} {cnt:3d} {typ:s}".format(nam=fo.name, nlength=nlength, \
                                                                                            typ=fo.objtype, lab=fo.label, mn=fo.mean, st=fo.std,
                                                                                            pc=fo.std*100.0/fo.mean, cnt=fo.count))
except (KeyboardInterrupt, BrokenPipeError):
    sys.exit(0)

nametolab = dict()
for fo in folist:
    nametolab[fo.name] = fo.label

for fil in files:
    findres = find_results.load_results_from_file(fil)
    if findres.filter not in filtlim:
        continue
    newresults = []
    for fr in findres.results(idonly=True, nohidden=True):
        try:
            lab = nametolab[fr.obj.objname]
            fr.label = fr.obj.label = lab
        except KeyError:
            fr.label = '?'
            fr.obj.label = None
        newresults.append(fr)
    findres.resultlist = newresults
    findres.relabel()
    try:
        find_results.save_results_to_file(findres, fil, force=True)
    except find_results.FindResultErr as e:
        print("Could not resave file, error was", e.args[0], file=sys.stderr)
        errors += 1

if errors > 0:
    print("Aborting due to", errors, "errors", file=sys.stderr)
    sys.exit(201)

print("Deleting old labels....", file=sys.stderr)
mycu.execute("UPDATE objdata SET label=NULL WHERE vicinity=%s", vicinity)
print("Installing new....", file=sys.stderr)
for fo in folist:
    mycu.execute("UPDATE objdata SET label=%s WHERE ind={:d}".format(fo.objind), fo.label)
print("Update complete", file=sys.stderr)
mydb.commit()
