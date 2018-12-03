#! /usr/bin/env python

# @Author: John M Collins <jmc>
# @Date:   2018-11-22T17:05:35+00:00
# @Email:  jmc@toad.me.uk
# @Filename: dblcurvegen.py
# @Last modified by:   jmc
# @Last modified time: 2018-12-02T22:43:37+00:00

import numpy as np
import argparse
import sys
import string
import datetime
import dbops
import dbobjinfo
import dbremfitsobj

def make_resultsrow(dat, adudict):
    """Make up results row"""
    global objnames
    r = [dat]
    for obn in objnames:
        try:
            p = adudict[obn]
        except KeyError:
            p = -1.0
        r.append(p)
    return r

parsearg = argparse.ArgumentParser(description='Plot light curves from ADU calcs', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('refobjs', type=str, nargs=1, help='Target name')
parsearg.add_argument('--filter', type=str, required=True, help='Filter to use')
parsearg.add_argument('--percentile', type=float, default=50.0, help='perecntile to subtract for sky level default median')
parsearg.add_argument('--outfile', type=str, help='Output file for results')

resargs = vars(parsearg.parse_args())
targetname = resargs['refobjs'][0]
filter = resargs['filter']
percentile = resargs['percentile']
outfile = resargs['outfile']

dbase = dbops.opendb('remfits')
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

p = "SELECT obsind,date_obs,objname,aducount FROM aducalc WHERE filter=" + dbase.escape(filter) + " AND percentile=%.3f" % percentile + " AND target=" + qtarg + " ORDER BY date_obs"
dbcurs.execute(p)
aduresults = dbcurs.fetchall()

results = []
last_obsind = -1
last_date = None

for obsind, dateobs, objname, aducount in aduresults:
    if obsind != last_obsind:
        if last_date is not None:
            results.append(make_resultsrow(last_date, aducounts))
        aducounts = dict()
        last_date = dateobs
        last_obsind = obsind
    aducounts[objname] = aducount

if last_date is not None:
    results.append(make_resultsrow(last_date, aducounts))

if len(results) < 2:
    print >>sys.stderr, "Not enough results to display"
    sys.exit(10)

if outfile is None:
    outf = sys.stdout
else:
    outf = open(outfile, 'wt')

lengths = [max(14,len(x)) for x in objnames]

print >>outf, "%-19s" % "-",
for l, obn in zip(lengths, objnames):
    print >>outf, "%*s" % (l, obn),
print >>outf

print >>outf, "%-19s" % "-",
for l, obn in zip(lengths, objnames):
    print >>outf, "%*d" % (l, objnums[obn]),

print >>outf

for r in results:
    dat = r.pop(0)
    print >>outf, dat.isoformat(),
    n = 0
    while len(r) != 0:
        v = r.pop(0)
        print >>outf,  "%*.7e" % (lengths[n], v),
        n += 1
    print >>outf
