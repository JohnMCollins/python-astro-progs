#! /usr/bin/env python3

from scipy import stats
import numpy as np
import argparse
import sys
import math
import string
import dbops
import remdefaults
import os
import os.path

mydbname = remdefaults.default_database()

parsearg = argparse.ArgumentParser(description='Get FITS inds from table using supplied mysql conditionl', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('--database', type=str, default=mydbname, help='Database to use')
parsearg.add_argument('--filter', type=str, help='Filter to use', required=True)
parsearg.add_argument('--table', type=str, default='iforbinf', help='Database table to use')
parsearg.add_argument('--condition', type=str, required=True, help='Condition to apply"')

resargs = vars(parsearg.parse_args())
mydbname = resargs['database']
filter = resargs['filter']
table = resargs['table']
condit = resargs['condition']

dbase = dbops.opendb(mydbname)
dbcurs = dbase.cursor()

dbcurs.execute("SELECT ind FROM " + table + " WHERE filter='" + filter + "' AND gain=1 AND ind!=0 AND (" + condit + ")")
rows = dbcurs.fetchall()

for r in rows:
    row, = r
    print(row)
