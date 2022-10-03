#!  /usr/bin/env python3

"""Remove suppressed objects from findres files"""

import argparse
import sys
import glob
import remdefaults
import find_results

parsearg = argparse.ArgumentParser(description='Remove suppressed objects in find results', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', nargs='*', type=str, help='Find results files or glob for them')
remdefaults.parseargs(parsearg, tempdir=False, inlib=False)

resargs = vars(parsearg.parse_args())
files = resargs['files']
remdefaults.getargs(resargs)

suppdict = set()
nonsupp = set()

totfrchanges = tofrfilesch = 0

dbase, curs = remdefaults.opendb()

if len(files) == 0:
    files = glob.iglob('*.findres')

for fil in files:
    try:
        findres = find_results.load_results_from_file(fil)
    except find_results.FindResultErr as e:
        print(fil, "gave error", e.args[0], file=sys.stderr)
        continue

    frchanges = 0

    for fr in findres.results(idonly=True):
        oname = fr.obj.objname

        if oname in nonsupp:
            continue

        if oname not in suppdict:
            curs.execute("SELECT suppress FROM objdata WHERE objname=%s", oname)
            r = curs.fetchone()
            if r is None:
                continue
            if r[0]:
                suppdict.add(oname)
            else:
                nonsupp.add(oname)
                continue

        fr.hide = True
        frchanges += 1

    if  frchanges == 0:
        continue

    totfrchanges += frchanges
    tofrfilesch += 1
    findres.resultlist = [fr for fr in findres.results(idonly=True) if not fr.hide]
    findres.reorder()
    findres.relabel()
    try:
        find_results.save_results_to_file(findres, fil, force=True)
    except find_results.FindResultErr as e:
        print("Saving", fil, "gave error", e.args[0], file=sys.stderr)

if totfrchanges != 0:
    print(totfrchanges, "changes in", tofrfilesch, "files", file=sys.stderr)
else:
    print("No changes made", file=sys.stderr)
