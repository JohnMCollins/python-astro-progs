#!  /usr/bin/env python

import dbops
import string
import datetime
import argparse
from operator import attrgetter

class obstot(object):
	"""Details of result"""

	def __init__(self, objname, n):
		self.objname = objname
		self.count = int(n)
		self.earliest = None
		self.latest = None

parsearg = argparse.ArgumentParser(description='List all objects with first and last date',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('--order', type=str, help='Order - (n)umber obs (e)arlist (l)atest')

resargs = vars(parsearg.parse_args())
order = resargs['order']

mydb = dbops.opendb('remfits')

dbcurs = mydb.cursor()

dbcurs.execute("SELECT object,COUNT(*) AS number FROM obs GROUP BY object")

results = []

for row in dbcurs.fetchall():
	obj, num = row
	results.append(obstot(obj, num))

for k in results:
	obj = k.objname
	dbcurs.execute("SELECT date_obs FROM obs WHERE object='" + obj + "' ORDER BY date_obs LIMIT 1")
	row = dbcurs.fetchall()
	k.fromdate = row[0][0]
	dbcurs.execute("SELECT date_obs FROM obs WHERE object='" + obj + "' ORDER BY date_obs DESC LIMIT 1")
	row = dbcurs.fetchall()
	k.todate = row[0][0]

if order is not None and len(order) != 0:
	f = string.lower(order)[0]
	if f == 'n':
		results.sort(key=attrgetter('count'),reverse=True)
	elif f == 'e':
		results.sort(key=attrgetter('fromdate'))
	elif f == 'l':
		results.sort(key=attrgetter('todate'),reverse=True)

for k in results:
	print "%-14s\t%d\t" % (k.objname, k.count) + k.fromdate.strftime("%d-%m-%y\t") + k.todate.strftime("%d-%m-%y")
