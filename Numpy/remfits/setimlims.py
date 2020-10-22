#! /usr/bin/env python3

# @Author: John M Collins <jmc>
# @Date:   2019-01-04T22:45:59+00:00
# @Email:  jmc@toad.me.uk
# @Filename: setgeom.py
# @Last modified by:   jmc
# @Last modified time: 2019-01-04T23:24:29+00:00

import argparse
import sys
import string
import remgeom
import dbops
import remdefaults

parsearg = argparse.ArgumentParser(description='Set up maximum limits for each filter from database', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
mydbname = remdefaults.default_database()
parsearg.add_argument('--database', type=str, default=mydbname, help='Database to use')
parsearg.add_argument('--latex', action='store_true', help='Latex output')
parsearg.add_argument('--outfile', type=str, help='Output file name for table')

resargs = vars(parsearg.parse_args())
mydbname = resargs['database']
latex = resargs['latex']
outfile = resargs['outfile']

rg = remgeom.load()

existingrows = dict()
existingcols = dict()

for filter in 'girz':
    il = rg.get_imlim(filter)
    existingrows[filter] = il.rows
    existingcols[filter] = il.cols

dbase = dbops.opendb(mydbname)
dbcurs = dbase.cursor()

dbcurs.execute("SELECT MIN(nrows),MIN(ncols),filter FROM obsinf WHERE nrows IS NOT NULL GROUP BY filter")
rows = dbcurs.fetchall()

obsrows = dict()
obscols = dict()

for minr, minc, filt in rows:
    obsrows[filt] = minr
    obscols[filt] = minc

dbcurs.execute("SELECT MIN(nrows),MIN(ncols),filter FROM iforbinf WHERE nrows IS NOT NULL GROUP BY filter")
rows = dbcurs.fetchall()

for minr, minc, filt in rows:
    try:
        if minr < obsrows[filt]:
            obsrows[filt] = minr
        if minc < obscols[filt]:
            obscols[filt] = minc
    except KeyError:
        obsrows[filt] = minr
        obscols[filt] = minc

changes = 0

for filter in 'girz':
    try:
        if obsrows[filter] != existingrows[filter]:
            existingrows[filter] = obsrows[filter]
            changes += 1
        if obscols[filter] != existingcols[filter]:
            existingcols[filter] = obscols[filter]
            changes += 1
    except KeyError:
        pass

if changes != 0:
    print(changes, "changes made")
    for filter in 'girz':
        il = remgeom.Imlimits(filter=filter, rows=existingrows[filter], cols=existingcols[filter])
        rg.set_imlim(il)
    remgeom.save(rg)

outf = sys.stdout
if outfile is not None:
    outf = open(outfile, "wt")

if latex:
    for filter in 'girz':
        print("\\texttt{" + filter + "}", existingrows[filter], existingcols[filter], sep=" & ", end=" \\\\\n", file=outf)
else:
    for filter in 'girz':
        print("%s %4d %4d" % (filter, existingrows[filter], existingcols[filter]), file=outf)
