#! /usr/bin/env python3

# @Author: John M Collins <jmc>
# @Date:   2018-11-22T17:05:35+00:00
# @Email:  jmc@toad.me.uk
# @Filename: dblcurvegen.py
# @Last modified by:   jmc
# @Last modified time: 2019-01-04T22:57:35+00:00

import numpy as np
import argparse
import sys
import string
import datetime
import dbops
import dbobjinfo
import dbremfitsobj
import remdefaults

def make_resultsrow(dat, ind, exptime, adudict):
    """Make up results row"""
    global objnames
    r = [dat, ind, exptime]
    for obn in objnames:
        try:
            p = adudict[obn]
        except KeyError:
            p = -1.0
        r.append(p)
    return r

parsearg = argparse.ArgumentParser(description='Plot light curves from ADU calcs', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('refobjs', type=str, nargs=1, help='Target name')
parsearg.add_argument('--database', type=str, default=remdefaults.default_database(), help='Database to use')
parsearg.add_argument('--filter', type=str, required=True, help='Filter to use')
parsearg.add_argument('--percentile', type=float, default=50.0, help='perecntile to subtract for sky level default median')
parsearg.add_argument('--outfile', type=str, help='Output file for results')

resargs = vars(parsearg.parse_args())
targetname = resargs['refobjs'][0]
dbname = resargs['database']
filter = resargs['filter']
percentile = resargs['percentile']
outfile = resargs['outfile']

dbase = dbops.opendb(dbname)
dbcurs = dbase.cursor()

targetname = dbobjinfo.get_targetname(dbcurs, targetname)
qtarg = dbase.escape(targetname)

dbcurs.execute("SELECT objname,COUNT(*) AS number FROM aducalc WHERE target=" + qtarg + " GROUP BY objname ORDER BY number DESC")
flist = dbcurs.fetchall()

objnames = []
objnums = dict()
for objname, num in flist:
    objnames.append(objname)
    objnums[objname] = num

p = "SELECT obsind,date_obs,objname,aducount,exptime FROM aducalc WHERE filter=" + dbase.escape(filter) + " AND percentile=%.3f" % percentile + " AND target=" + qtarg + " ORDER BY date_obs"
dbcurs.execute(p)
aduresults = dbcurs.fetchall()

results = []
last_obsind = -1
last_exptime = None
last_date = None

for obsind, dateobs, objname, aducount, exptime in aduresults:
    if obsind != last_obsind:
        if last_date is not None:
            results.append(make_resultsrow(last_date, last_obsind, last_exptime, aducounts))
        aducounts = dict()
        last_date = dateobs
        last_obsind = obsind
        last_exptime = exptime
    aducounts[objname] = aducount

if last_date is not None:
    results.append(make_resultsrow(last_date, last_obsind, last_exptime, aducounts))

if len(results) < 2:
    print("Not enough results to display", file=sys.stderr)
    sys.exit(10)

if outfile is None:
    outf = sys.stdout
else:
    outf = open(outfile, 'wt')

lengths = [max(14,len(x)) for x in objnames]

print("%-19s" % "-","%8s" % '-', "xxx", end=' ', file=outf)
for l, obn in zip(lengths, objnames):
    print("%*s" % (l, obn), end=' ', file=outf)
print(file=outf)

print("%-19s" % "-","%8s" % '-', "xxx", end=' ', file=outf)
for l, obn in zip(lengths, objnames):
    print("%*d" % (l, objnums[obn]), end=' ', file=outf)

print(file=outf)

for r in results:
    dat = r.pop(0)
    obsind = r.pop(0)
    exptime = r.pop(0)
    print(dat.isoformat(), "%8d" % obsind, "%.1f" % exptime, end=' ', file=outf)
    n = 0
    while len(r) != 0:
        v = r.pop(0)
        print("%*.7e" % (lengths[n], v), end=' ', file=outf)
        n += 1
    print(file=outf)
