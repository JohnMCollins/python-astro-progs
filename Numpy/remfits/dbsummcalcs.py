#! /usr/bin/env python

# @Author: John M Collins <jmc>
# @Date:   2018-11-22T17:05:35+00:00
# @Email:  jmc@toad.me.uk
# @Filename: dblcurvegen.py
# @Last modified by:   jmc
# @Last modified time: 2018-12-02T10:15:44+00:00

import numpy as np
import argparse
import sys
import string
import datetime
import parsetime
import dbops
import dbobjinfo
import dbremfitsobj

parsearg = argparse.ArgumentParser(description='Summarise reference objects in ADU calcs', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('target', type=str, nargs=1, help='Target object (or alias)')

resargs = vars(parsearg.parse_args())
target = resargs['target']

dbase = dbops.opendb('remfits')
dbcurs = dbase.cursor()

targetname = dbobjinfo.get_targetname(dbcurs, target[0])
qtarg = dbase.escape(targetname)

dbcurs.execute("SELECT objname,COUNT(*) AS number FROM aducalc WHERE target=" + qtarg + " GROUP BY objname ORDER BY number DESC")
flist = dbcurs.fetchall()

nlen = max([0] + [len(p[0]) for p in flist])

for name, num in flist:
    print name, " " * (nlen - len(name)), "%5d" % num
