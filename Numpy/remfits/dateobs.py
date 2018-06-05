#!  /usr/bin/env python

import dbops
import argparse
import string
import datetime
import re
import sys

parsearg = argparse.ArgumentParser(description='List dates on which given object was observed',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parsearg.add_argument('object', type=str, nargs=1, help='Object we are talking about')
resargs = vars(parsearg.parse_args())

obj = resargs['object'][0]

mydb = dbops.opendb('remfits')
dbcurs = mydb.cursor()
dbcurs.execute("SELECT date(date_obs),count(*) FROM obsinf WHERE object='" + obj + "' GROUP BY date(date_obs)")
for row in dbcurs.fetchall():
    dat,cnt = row
    print "%s\t%d" % (dat.strftime("%Y-%m-%d"), cnt)
