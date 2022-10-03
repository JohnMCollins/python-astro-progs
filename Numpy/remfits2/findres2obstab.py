#!  /usr/bin/env python3

"""Generate table of dates/obs for display"""

import argparse
import sys
import numpy as np
import remdefaults
import find_results
import col_from_file
import miscutils
import parsetime

parsearg = argparse.ArgumentParser(description='Generate table from findres files', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', nargs='*', type=str, help='Find results files or take from stdin')
parsearg.add_argument('--colnum', type=int, default=0, help='Column number to take from standard input')
remdefaults.parseargs(parsearg, tempdir=False, inlib=False)
parsearg.add_argument('--daterange', type=str, help='Range of dates to limit to')
parsearg.add_argument('--outfile', type=str, help='Output file or use stdout')
parsearg.add_argument('--filter', type=str, help='Filter name to limit to')
parsearg.add_argument('--verbose', action='store_true', help='Give blow-by-blow account')

resargs = vars(parsearg.parse_args())
files = resargs['files']
if len(files) == 0:
    files = col_from_file.col_from_file(sys.stdin, resargs['colnum'])
files = sorted(set(files))
if len(files) < 10:
    print("Not worth doing with only", len(files), "files", file=sys.stderr)
    sys.exit(10)

remdefaults.getargs(resargs)
daterange = resargs['daterange']

if daterange is not None:
    dr = parsetime.DateRangeArg()
    try:
        dr.parsearg(daterange)
    except ValueError as e:
        print(e.args[0], file=sys.stderr)
        sys.exit(30)
    daterange = dr

filtonly = resargs['filter']
verbose = resargs['verbose']
outfile = resargs['outfile']

mydb, dbcurs = remdefaults.opendb()

errors = 0
rtab = []

for fil in files:
    try:
        findres = find_results.load_results_from_file(fil)
    except find_results.FindResultErr as e:
        print(fil, "gave error", e.args[0], file=sys.stderr)
        errors += 1
        continue
    if daterange and not daterange.inrange(findres.obsdate):
        if verbose:
            print("File {:s} date of {:%d/%m/%Y} outside range".format(fil, findres.obsdate), file=sys.stderr)
        continue
    if filtonly and filtonly != findres.filter:
        if verbose:
            print("File {:s} filter {:s} not accepted".format(fil, findres.filter), file=sys.stderr)
        continue
    if findres.num_results(idonly=True, nohidden=True) == 0:
        if verbose:
            print("No results in file {:s}".format(fil), file=sys.stderr)
        continue
    fr = findres[0]
    if not fr.istarget:
        if verbose:
            print("First result in file {:s} not target".format(fil), file=sys.stderr)
        continue
    dbcurs.execute("SELECT bjdobs FROM obsinf WHERE obsind={:d}".format(findres.obsind))
    dbres = dbcurs.fetchone()
    if dbres is None:
        print("Cannot find obsind {:d} in file {:s}".format(findres.obsind, fil), file=sys.stderr)
        errors += 1
        continue
    rtab.append((dbres[0], fr.adus))

if len(rtab) < 10:
    print("Not onough resutts {:d} to continue".format(len(rtab)), file=sys.stderr)
    sys.exit(20)
if errors != 0:
    print("Aborting due to", errors, "errors", file=sys.stderr)
    sys.exit(30)

if outfile is None:
    outfile = sys.stdout
else:
    outfile = miscutils.addsuffix(outfile, "txt")

np.savetxt(outfile, rtab)
