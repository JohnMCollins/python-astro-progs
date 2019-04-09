#!  /usr/bin/env python3

# @Author: John M Collins <jmc>
# @Date:   2019-01-04T22:45:55+00:00
# @Email:  jmc@toad.me.uk
# @Filename: dateobs.py
# @Last modified by:   jmc
# @Last modified time: 2019-01-04T22:50:21+00:00

import dbops
import remdefaults
import argparse
import string
import datetime
import re
import sys

parsearg = argparse.ArgumentParser(description='List dates on which given object was observed',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parsearg.add_argument('object', type=str, nargs=1, help='Object we are talking about')
parsearg.add_argument('--database', type=str, default=remdefaults.default_database(), help='Database to use')
resargs = vars(parsearg.parse_args())

obj = resargs['object'][0]
dbname = resargs['database']

mydb = dbops.opendb(dbname)
dbcurs = mydb.cursor()
dbcurs.execute("SELECT date(date_obs),count(*) FROM obsinf WHERE object='" + obj + "' GROUP BY date(date_obs)")
for row in dbcurs.fetchall():
    dat,cnt = row
    print("%s\t%d" % (dat.strftime("%Y-%m-%d"), cnt))
