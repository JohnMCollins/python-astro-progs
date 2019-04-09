#!  /usr/bin/env python3

# @Author: John M Collins <jmc>
# @Date:   2019-01-04T22:45:58+00:00
# @Email:  jmc@toad.me.uk
# @Filename: listobjects.py
# @Last modified by:   jmc
# @Last modified time: 2019-01-04T23:10:43+00:00

import dbops
import remdefaults
import datetime
import argparse
from operator import attrgetter
import dbobjinfo
import numpy as np
import locale

def thou(n):
    """Print n with thousands separator"""
    return locale.format_string("%d", n, grouping=True)

class obstot(object):
	"""Details of result"""

	def __init__(self, objname, n):
		self.objname = objname
		self.count = int(n)
		self.fromdate = None
		self.todate = None
		self.isundef = None

parsearg = argparse.ArgumentParser(description='List number by filter',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('--database', type=str, default=remdefaults.default_database(), help='Database to use')
parsearg.add_argument('--latex', action='store_true', help='Latex output')

resargs = vars(parsearg.parse_args())
dbname = resargs['database']
latex = resargs['latex']

mydb = dbops.opendb(dbname)

dbcurs = mydb.cursor()

dbcurs.execute("SELECT filter,COUNT(*) FROM obsinf GROUP BY filter")

results = dict()

for row in dbcurs.fetchall():
	filter, count = row
	results[filter] = count

if latex:
    locale.setlocale(locale.LC_ALL, "")
    for filter in 'girzHJK':
        print(filter, thou(results[filter]), sep=' & ', end=' \\\\\n')
    print('GRISM', thou(results['GRI']), sep=' & ', end=' \\\\\n')

else:
    for filter in 'girzHJK':
        print("%s\t%7d" % (filter, results[filter]))
    print("%s\t%7d" % ('GRISM', results['GRI']))
