#! /usr/bin/env python

# @Author: John M Collins <jmc>
# @Date:   2018-11-22T17:05:35+00:00
# @Email:  jmc@toad.me.uk
# @Filename: dblcurvegen.py
# @Last modified by:   jmc
# @Last modified time: 2018-11-22T21:27:44+00:00

import numpy as np
import argparse
import sys
import string
import datetime
import dbops
import dbobjinfo
import dbremfitsobj

parsearg = argparse.ArgumentParser(description='Plot light curves from ADU calcs', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('refobjs', type=str, nargs='+', help='Target then reference object names')
parsearg.add_argument('--filter', type=str, required=True, help='Filter to use')
parsearg.add_argument('--percentile', type=float, default=50.0, help='perecntile to subtract for sky level default median')
parsearg.add_argument('--outfile', type=str, required=True, help='Output file for display')

resargs = vars(parsearg.parse_args())
refobjs = resargs['refobjs']
filter = resargs['filter']
percentile = resargs['percentile']
outfile = resargs['outfile']

if len(refobjs) < 2:
    print >>sys.stderr, "Usage: must have target and at least one reference object as args"
    sys.exit(100)

dbase = dbops.opendb('remfits')
dbcurs = dbase.cursor()

# We'll just do the one reference object for Now

targetname = dbobjinfo.get_targetname(dbcurs, refobjs[0])
refname = dbobjinfo.get_targetname(dbcurs, refobjs[1])

qtarg = dbase.escape(targetname)
qref = dbase.escape(refname)

p = "SELECT obsind,date_obs,objname,aducount FROM aducalc WHERE filter=" + dbase.escape(filter) + " AND percentile=%.3f" % percentile + " AND target=" + qtarg + " AND (objname=" + qtarg + " OR objname=" + qref + ") ORDER BY date_obs"
print >>sys.stderr, p
dbcurs.execute(p)
aduresults = dbcurs.fetchall()

results = []
last_obsind = -1
last_targ = -1
last_ref = -1
last_date = 0

for obsind, dateobs, objname, aducount in aduresults:
    if obsind != last_obsind:
        if last_targ > 0 and last_ref > 0:
            results.append((last_date, last_targ / last_ref, last_obsind))
        last_targ = -1
        last_ref = -1
        last_date = dateobs
        last_obsind = obsind
    if objname != targetname:
        last_ref = aducount
    else:
        last_targ = aducount

if last_targ > 0 and last_ref > 0:
    results.append((last_date, last_targ / last_ref, last_obsind))

if len(results) < 2:
    print >>sys.stderr, "Not enough to display"
    sys.exit(10)

outf = open(outfile, 'wt')
for dat, adus, obsind in results:
    outf.write(dat.strftime("%Y-%m-%d %H-%M-%S") + " %.6g %d\n" % (adus, obsind))
outf.close()
