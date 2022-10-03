#!  /usr/bin/env python3

"""Generate table of Barycentric dates and ADU counts ready for periodogram"""

import argparse
import glob
import sys
import numpy as np
import remdefaults
import find_results
import miscutils

parsearg = argparse.ArgumentParser(description='Generate table of findres results from prefix', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', nargs='+', type=str, help='Find results or prefix(es)')
remdefaults.parseargs(parsearg, tempdir=False, inlib=False)
parsearg.add_argument('--byprefix', action='store_true', help='Arguments are prefixes not file names')
parsearg.add_argument('--outfile', type=str, required=True, help='Output file name')

resargs = vars(parsearg.parse_args())
files = resargs['files']
byprefix = resargs['byprefix']
remdefaults.getargs(resargs)
outfile = miscutils.addsuffix(resargs['outfile'], 'txt')

files_to_do = set()

if byprefix:

    for f in files:
        files_to_do |= set(glob.glob(f + '*.findres'))

else:
    files_to_do |= set(files)

reslist = []
for f in files_to_do:
    findres = find_results.load_results_from_file(f)
    if findres.num_results(idonly=True, nohidden=True) == 0:
        continue
    fr = findres[0]
    if not fr.istarget:
        continue
    reslist.append((findres.obsind, fr.adus))

db, cu = remdefaults.opendb()

resarray = []

for obsind, adus in reslist:
    cu.execute("SELECT bjdobs FROM obsinf WHERE obsind={:d}".format(obsind))
    r = cu.fetchone()
    resarray.append((r[0], adus))

np.savetxt(outfile, np.array(resarray))
print(len(resarray), "Results listed", file=sys.stderr)
