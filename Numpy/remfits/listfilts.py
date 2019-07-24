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
parsearg.add_argument('--objects', type=str, nargs='*', help='Objects to limit to')
parsearg.add_argument('--latex', action='store_true', help='Latex output')

resargs = vars(parsearg.parse_args())
dbname = resargs['database']
objlist = resargs['objects']
latex = resargs['latex']

mydb = dbops.opendb(dbname)

dbcurs = mydb.cursor()

sel = ''
if objlist is not None:
    qobj = [ "object='" + o + "'" for o in objlist]
    sel = " WHERE (" + " OR ".join(qobj) +")"

dbcurs.execute("SELECT filter,COUNT(*) FROM obsinf" + sel + " GROUP BY filter")

results = dict()

for row in dbcurs.fetchall():
	filter, count = row
	results[filter] = count

if latex:
    locale.setlocale(locale.LC_ALL, "")
    for filter in 'girzHJK':
        print(filter, thou(results[filter]), sep=' & ', end=' \\\\\n')
    try:
        print('GRISM', thou(results['GRI']), sep=' & ', end=' \\\\\n')
    except KeyError:
        pass

else:
    for filter in 'girzHJK':
        print("%s\t%7d" % (filter, results[filter]))
    try:
        print("%s\t%7d" % ('GRISM', results['GRI']))
    except KeyError:
        pass
