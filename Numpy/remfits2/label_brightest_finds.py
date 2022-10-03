#!  /usr/bin/env python3

"""Apply labels to brightest objects found"""

import argparse
import sys
import remdefaults
import find_results

parsearg = argparse.ArgumentParser(description='Provide labels to brightest objects found', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('file', nargs=1, type=str, help='Findres file')
remdefaults.parseargs(parsearg, tempdir=False, inlib=False)
parsearg.add_argument('--minmag', type=float, default=15.0, help='Minimum magnitude to find')
parsearg.add_argument('--filter', type=str, help='Filter to limit to otherwise take brightest')
parsearg.add_argument('--verbose', action='store_true', help='Tell everything')

resargs = vars(parsearg.parse_args())
file = resargs['file'][0]
minmag = resargs['minmag']
filt = resargs['filter']
verbose = resargs['verbose']

if filt is None:
    magset = set('griz')
else:
    magset = set(filt)

mydb, dbcurs = remdefaults.opendb()

try:
    findres = find_results.load_results_from_file(file)
    targfr = findres.get_targobj()
except find_results.FindResultErr as e:
    print("Cannot open", file, "error was", e.args[0], file=sys.stderr)
    sys.exit(10)

already_got = findres.get_label_set(dbcurs)
mag_to_fr = dict()
for fr in findres.results(idonly=True):
    if fr.obj.valid_label():
        continue
    mag = 1e9           # Should be a lesser value than that
    for m in magset:
        mf = getattr(fr.obj, m + 'mag', None)
        if mf is not None  and  mf < mag:
            mag = mf
    if mag < minmag:
        if mag in mag_to_fr:
            mag_to_fr[mag].append(fr)
        else:
            mag_to_fr[mag] = [fr]

if len(mag_to_fr) == 0:
    print("No labels to assign in", file, file=sys.stderr)
    sys.exit(11)

for mag in sorted(mag_to_fr.keys()):
    for fr in mag_to_fr[mag]:
        fr.assign_label(dbcurs, already_got)        # NB updates already_got
        if verbose:
            print("Assigned label", fr.label, "to", fr.obj.dispname, file=sys.stderr)

findres.reorder()
findres.relabel()
find_results.save_results_to_file(findres, file, force=True)
mydb.commit()
