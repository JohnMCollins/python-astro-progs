#! /usr/bin/env python3

# @Author: John M Collins <jmc>
# @Date:   2018-11-22T17:05:35+00:00
# @Email:  jmc@toad.me.uk
# @Filename: dblcurvegen.py
# @Last modified by:   jmc
# @Last modified time: 2019-01-04T22:54:39+00:00

import numpy as np
import argparse
import sys
import string
import datetime
import parsetime
import dbops
import remdefaults
import dbobjinfo
import dbremfitsobj

parsearg = argparse.ArgumentParser(description='Summarise reference objects in ADU calcs', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('--database', type=str, default=remdefaults.default_database(), help='Database to use')
parsearg.add_argument('target', type=str, nargs=1, help='Target object (or alias)')

resargs = vars(parsearg.parse_args())
target = resargs['target']
dbname = resargs['database']

dbase = dbops.opendb(dbname)
dbcurs = dbase.cursor()

targetname = dbobjinfo.get_targetname(dbcurs, target[0])
qtarg = dbase.escape(targetname)

dbcurs.execute("SELECT objname,COUNT(*) AS number FROM aducalc WHERE target=" + qtarg + " GROUP BY objname ORDER BY number DESC")
flist = dbcurs.fetchall()

nlen = max([0] + [len(p[0]) for p in flist])

for name, num in flist:
    print(name, " " * (nlen - len(name)), "%5d" % num)
